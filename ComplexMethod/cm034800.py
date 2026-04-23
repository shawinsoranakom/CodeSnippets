def stream_read_parts_and_refine(bucket_dir: Path, delete_files: bool = False) -> Iterator[str]:
    cache_file = bucket_dir / PLAIN_CACHE
    space_file = Path(bucket_dir) / f"spacy_0001.cache"
    part_one = bucket_dir / f"plain_0001.cache"
    if not space_file.exists() and not part_one.exists() and cache_file.exists():
        split_file_by_size_and_newline(cache_file, bucket_dir)
    for idx in range(1, 1000):
        part = bucket_dir / f"plain_{idx:04d}.cache"
        tmp_file = Path(bucket_dir) / f"spacy_{idx:04d}.{time.time()}.tmp"
        cache_file = Path(bucket_dir) / f"spacy_{idx:04d}.cache"
        if cache_file.exists():
            with open(cache_file, "r") as f:
                yield f.read(errors="replace")
            continue
        if not part.exists():
            break
        with tmp_file.open("w") as f:
            for chunk in spacy_refine_chunks(read_path_chunked(part)):
                f.write(chunk)
                yield chunk
        tmp_file.rename(cache_file)
        if delete_files:
            part.unlink()