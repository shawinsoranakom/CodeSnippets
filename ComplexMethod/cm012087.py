def iterate_over_candidates(
        cls: type[GuardedCache[T]],
        local: bool,
        remote_cache: RemoteCache[JsonDataTy] | None,
        key: str,
    ) -> Generator[tuple[T, bytes, bool], None, None]:
        if local:
            subdir = cls._get_tmp_dir_for_key(key)
            if os.path.exists(subdir):
                for path in sorted(os.listdir(subdir)):
                    if path.startswith("."):
                        continue  # Skip temp files from concurrent write_atomic() calls
                    try:
                        with open(os.path.join(subdir, path), "rb") as f:
                            content = f.read()
                            yield pickle.loads(content), content, True
                    except Exception:
                        log.warning(
                            "fx graph cache unable to load compiled graph",
                            exc_info=True,
                        )

        if remote_cache:
            try:
                if (cache_data := remote_cache.get(key)) is not None:
                    assert isinstance(cache_data, dict)
                    data = cache_data["data"]
                    assert isinstance(data, (str, bytes))
                    content = base64.b64decode(data)
                    yield pickle.loads(content), content, False
            except Exception:
                log.warning(
                    "%s unable to load compiled graph", cls.__name__, exc_info=True
                )