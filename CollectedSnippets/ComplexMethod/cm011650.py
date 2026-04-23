def fresh_cache(
    cache_entries: dict[str, Any] | None = None,
    dir: str | None = None,
    delete: bool = True,
) -> Iterator[None]:
    """
    Contextmanager that provides a clean tmp cachedir for pt2 caches.

    Optionally, pass a dict as 'cache_entries' to get a list of filenames and sizes
    generated with this cache instance.
    """
    clear_caches()

    from torch._inductor.cpp_builder import normalize_path_separator

    inductor_cache_dir = normalize_path_separator(tempfile.mkdtemp(dir=dir))
    try:
        with _set_env("TORCHINDUCTOR_CACHE_DIR", inductor_cache_dir):
            log.debug("Using inductor cache dir %s", inductor_cache_dir)
            triton_cache_dir = normalize_path_separator(
                os.path.join(inductor_cache_dir, "triton")
            )
            with _set_env("TRITON_CACHE_DIR", triton_cache_dir):
                yield
                if isinstance(cache_entries, dict):
                    assert len(cache_entries) == 0, "expected empty cache_entries dict"
                    if os.path.exists(triton_cache_dir):
                        files = os.listdir(triton_cache_dir)
                        cache_entries.update(
                            {
                                f: os.path.getsize(os.path.join(triton_cache_dir, f))
                                for f in files
                                if ".lock" not in f
                            }
                        )
        if delete:
            if is_windows() and torch.xpu.is_available():
                unload_xpu_triton_pyds()

            shutil.rmtree(
                inductor_cache_dir,
                # Let's not fail if we can't clean up the temp dir. Also note that for
                # Windows, we can't delete the loaded modules because the module binaries
                # are open.
                ignore_errors=is_windows(),
                onerror=lambda func, path, exc_info: log.warning(
                    "Failed to remove temporary cache dir at %s",
                    inductor_cache_dir,
                    exc_info=exc_info,
                ),
            )
    except Exception:
        log.warning("on error, temporary cache dir kept at %s", inductor_cache_dir)
        raise
    finally:
        clear_caches()