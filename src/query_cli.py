"""
query_cli.py — command-line entry point for querying
=========================================================
Thin CLI: parse args, drain QueryService's streaming generator into a
QueryResult, print it. No LlamaIndex/Qdrant logic lives here — see
services/query_service.py and the query/ package for that.

Renamed from the original query.py — that name would collide with the
query/ package directory (Python can't cleanly resolve `import query`
when both query.py and query/ exist side by side), so this layer needed
a distinct name. ingest_cli.py was renamed to match for consistency.

Usage (standalone test):
    python src/query_cli.py
    python src/query_cli.py --file research.pdf --question "What problem does this paper solve?"
    python src/query_cli.py --list

BUG FIX vs. the original: query.py's own main() did
`result = search(args.question)` and then `format_result(result)` —
but search()/summarize() are generator functions. Calling one just
returns a generator object immediately; it never produces a
QueryResult. format_result() then tries to read result.mode,
result.answer, etc. off that generator, which don't exist — so the
original "standalone test" CLI path raised an AttributeError on every
single run. _collect() below actually drains the generator (token by
token, capturing the final sources/elapsed) before building the
QueryResult that format_result() expects.
"""

import argparse

from query.models import QueryResult, SourceNode
from services.query_service import QueryService


def _collect(token_stream, mode: str, query: str) -> QueryResult:
    """Drain a streaming (token, sources, elapsed, is_done) generator into one QueryResult."""
    answer = ""
    sources: list[SourceNode] = []
    elapsed = 0.0
    error = None

    for token, srcs, elapsed, is_done in token_stream:
        if is_done:
            sources = srcs
            if token.startswith("**Error:**"):
                error = token
        else:
            answer += token

    return QueryResult(answer=answer, mode=mode, query=query, sources=sources, elapsed_sec=elapsed, error=error)


def format_result(result: QueryResult) -> str:
    """Pretty-print a QueryResult to the terminal."""
    lines = [
        "",
        f"{'='*60}",
        f"  Mode    : {result.mode}",
        f"  Query   : {result.query}",
        f"  Elapsed : {result.elapsed_sec}s",
        f"{'='*60}",
        "",
        result.answer,
        "",
    ]
    if result.sources:
        lines.append(f"{'─'*60}")
        lines.append("  Sources:")
        for s in result.sources:
            lines.append(
                f"    [{s.score:.3f}]  {s.filename}  "
                f"[{s.section}, p.{s.page}]"
            )
            lines.append(f"             \"{s.preview}...\"")
    if result.error:
        lines.append(f"\n  ERROR: {result.error}")
    lines.append(f"{'='*60}\n")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the Research Paper Summarizer")
    parser.add_argument("--question", "-q", type=str,
                         default="What is this paper about?",
                         help="Question to ask")
    parser.add_argument("--file", "-f", type=str, default=None,
                         help="Filename to summarize (e.g. research.pdf). "
                              "If omitted, searches across all papers.")
    parser.add_argument("--list", "-l", action="store_true",
                         help="List all indexed papers and exit")
    args = parser.parse_args()

    query_service = QueryService()

    if args.list:
        papers = query_service.list_papers()
        if papers:
            print("\nIndexed papers:")
            for p in papers:
                print(f"  - {p}")
        else:
            print("No papers indexed yet. Run: python src/ingest_cli.py")
        return

    if args.file:
        result = _collect(query_service.summarize(args.file, args.question), "summarize", args.question)
    else:
        result = _collect(query_service.search(args.question), "search", args.question)

    print(format_result(result))


if __name__ == "__main__":
    main()