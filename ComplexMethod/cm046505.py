def _preflight(
    repo_files,
    cached_files,
    free_bytes,
    hf_repo = "unsloth/Example-GGUF",
    hf_token = None,
):
    """Run the preflight arithmetic as written in llama_cpp.py and return
    the decision outcome as a dict.

    ``repo_files``: list of (filename, remote_bytes).
    ``cached_files``: dict {filename: on_disk_bytes} for files already in cache.
    ``free_bytes``: value returned by shutil.disk_usage(cache_dir).free.
    """
    import os
    import shutil

    path_infos = [_FakePathInfo(name, size) for name, size in repo_files]

    with tempfile.TemporaryDirectory() as tmp:
        # Create SPARSE files for the cached ones so os.path.exists /
        # os.path.getsize pass without actually allocating bytes on disk.
        # This is critical when simulating multi-GB models.
        cache_paths = {}
        for name, sz in cached_files.items():
            p = Path(tmp) / name.replace("/", "_")
            with open(p, "wb") as fh:
                if sz > 0:
                    fh.truncate(sz)  # sparse allocation: no data blocks written
            cache_paths[name] = str(p)

        def fake_try_to_load_from_cache(repo_id, filename):
            return cache_paths.get(filename)

        # Mirror the same variable names and control flow as the real code
        # so behavioral drift is caught immediately.
        total_bytes = sum((p.size or 0) for p in path_infos)
        already_cached_bytes = 0
        for p in path_infos:
            if not p.size:
                continue
            cached_path = fake_try_to_load_from_cache(hf_repo, p.path)
            if isinstance(cached_path, str) and os.path.exists(cached_path):
                try:
                    on_disk = os.path.getsize(cached_path)
                except OSError:
                    on_disk = 0
                if on_disk >= p.size:
                    already_cached_bytes += p.size

        total_download_bytes = max(0, total_bytes - already_cached_bytes)
        needed_download = total_download_bytes > free_bytes
        return {
            "total_bytes": total_bytes,
            "already_cached_bytes": already_cached_bytes,
            "total_download_bytes": total_download_bytes,
            "would_raise_disk_error": (needed_download and total_download_bytes > 0),
        }