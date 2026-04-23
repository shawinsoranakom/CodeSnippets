def _get_block_total_size(block_dir: Path, file_ids: list[str]) -> int:
    """Sum raw upload sizes for tracked file IDs only."""
    if not block_dir.exists() or not file_ids:
        return 0
    id_set = set(file_ids)
    total = 0
    for f in block_dir.iterdir():
        if not f.is_file():
            continue
        if f.name.endswith(".extracted.txt") or f.name.endswith(".meta.json"):
            continue
        stem = f.name.split(".")[0]
        if stem in id_set:
            total += f.stat().st_size
    return total