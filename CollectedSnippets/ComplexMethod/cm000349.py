def load_views(only: list[str] | None = None) -> list[tuple[str, str]]:
    """Return [(label, sql)] for all views, in alphabetical order."""
    files = sorted(QUERIES_DIR.glob("*.sql"))
    if not files:
        print(f"No .sql files found in {QUERIES_DIR}", file=sys.stderr)
        sys.exit(1)
    known = {f.stem for f in files}
    if only:
        unknown = [n for n in only if n not in known]
        if unknown:
            print(
                f"Unknown view name(s): {', '.join(unknown)}\n"
                f"Available: {', '.join(sorted(known))}",
                file=sys.stderr,
            )
            sys.exit(1)
    result = []
    for f in files:
        name = f.stem
        if only and name not in only:
            continue
        result.append((f"view analytics.{name}", build_view_sql(name, f.read_text())))
    return result