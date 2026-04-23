def _parse_jsonl(content: str) -> Any:
    lines = [json.loads(line) for line in content.splitlines() if line.strip()]
    if not lines:
        return content

    # When every line is a dict with the same keys, convert to table format
    # (header row + data rows) — consistent with CSV/TSV/Parquet/Excel output.
    # Require ≥2 dicts so a single-line JSONL stays as [dict] (not a table).
    if len(lines) >= 2 and all(isinstance(obj, dict) for obj in lines):
        keys = list(lines[0].keys())
        # Cache as tuple to avoid O(n×k) list allocations in the all() call.
        keys_tuple = tuple(keys)
        if keys and all(tuple(obj.keys()) == keys_tuple for obj in lines[1:]):
            return [keys] + [[obj[k] for k in keys] for obj in lines]

    return lines