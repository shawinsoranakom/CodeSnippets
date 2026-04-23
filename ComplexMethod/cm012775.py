def begin_compile(
        cls,
        inductor_meta: _InductorMetaTy,
        *,
        code: str | None = None,
        code_hash: str | None = None,
    ) -> None:
        assert cls._bundler is None

        if code is not None:
            assert code_hash is None, "Cannot specify both code and code_hash"
            code_hash = _comment_stripped_hash(code)
        assert code_hash is not None

        if not _AutotuneCacheBundlerImpl._should_use_bundled_autotune_remote_cache(
            inductor_meta
        ):
            return

        cache = create_cache(
            "bundled-autotune-v1",
            _AutotuneCacheBundlerImpl._get_is_fbcode(inductor_meta),
            "FbRemoteBundledAutotuneCache",
            "RemoteBundledAutotuneCache",
        )
        if not cache:
            return

        # We're starting a compilation phase. We have a cache key for the code
        # we're compiling. We'll get the individual autotune bundles later (via
        # self.put()). For now create the AutotuneCacheBundler and try to load
        # from the cache.

        salt = "bundled-autotune-best-configs-v1"
        backend_hash = _AutotuneCacheBundlerImpl._get_backend_hash(inductor_meta)
        # TODO: The autotune cache includes configs_hash in the key. The problem
        # is that the configs_hash includes info from the individual pointwise()
        # calls (size_hints, for example) which we can't know yet. I *think*
        # that info is basically present in the `code_hash` (since it's a
        # parameter to the pointwise decorator) - but is there other info we
        # need to include from inductor_meta?
        key = AUTOTUNE_CACHE_KEY_STRATEGY.key(code_hash, backend_hash, salt)

        bundler = _AutotuneCacheBundlerImpl(key, cache)
        if not bundler._load_cache():
            # We couldn't load from the cache - so save the data so we can store
            # the saved autotunes.
            cls._bundler = bundler