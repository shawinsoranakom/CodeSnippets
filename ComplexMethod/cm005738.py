def matches_pattern(file_path: str, pattern: str) -> bool:
    """Check if a file matches a glob pattern using pathlib semantics.

    Supports ** and a simple one-level {a,b} brace expansion.
    """
    import re
    from pathlib import PurePosixPath

    # Normalize
    file_path = file_path.lstrip("./").replace("\\", "/")
    pattern = pattern.lstrip("./")

    # Simple one-level brace expansion: foo.{ts,tsx} -> [foo.ts, foo.tsx]
    patterns = [pattern]
    m = re.search(r"\{([^{}]+)\}", pattern)
    if m:
        opts = [opt.strip() for opt in m.group(1).split(",")]
        pre, post = pattern[: m.start()], pattern[m.end() :]
        patterns = [f"{pre}{opt}{post}" for opt in opts]

    # PurePosixPath.match() only does relative matching from the right
    # For patterns with **, we need full path matching
    for pat in patterns:
        if "**" in pat:
            # Use fnmatch-style matching for ** patterns
            # Convert ** to match any depth
            import fnmatch

            regex_pattern = pat.replace("**", "*")
            if fnmatch.fnmatch(file_path, regex_pattern):
                return True
        else:
            # Use pathlib matching for non-** patterns
            p = PurePosixPath(file_path)
            if p.match(pat):
                return True

    return False