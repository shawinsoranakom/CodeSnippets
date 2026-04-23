def gh_api(endpoint: str) -> list | dict:
    """Call gh api with pagination and return parsed JSON."""
    result = subprocess.run(
        ["gh", "api", endpoint, "--paginate"],
        capture_output=True,
        text=True,
        check=True,
    )
    # --paginate may return multiple JSON arrays concatenated; we need to handle that
    # gh api --paginate with --jq is cleaner, but let's parse raw output
    # When paginating, gh outputs one JSON array per page on separate "lines"
    output = result.stdout.strip()
    if not output:
        return []

    # Try parsing as a single JSON value first
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        pass

    # If that fails, it's multiple JSON arrays concatenated
    # Split on ][ boundaries and merge
    all_items = []
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(output):
        # Skip whitespace
        while pos < len(output) and output[pos] in " \t\n\r":
            pos += 1
        if pos >= len(output):
            break
        obj, end_pos = decoder.raw_decode(output, pos)
        if isinstance(obj, list):
            all_items.extend(obj)
        else:
            all_items.append(obj)
        pos = end_pos
    return all_items