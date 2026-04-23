def _cached_dispatch_impl(
        self,
        func: OpOverload,
        types: Sequence[type],
        args: Sequence[object],
        kwargs: Mapping[str, object],
    ) -> object:
        """
        Lookup a cache entry for the given arguments. If none exists, dispatch
        and cache the result (if the result is eligible for caching).
        """
        state = None
        key = None
        try:
            state = _CacheKeyState(self.shape_env)
            key = self._cache_key(state, func, args, kwargs)
        except _BypassDispatchCache as e:
            # We couldn't create the cache key at all
            if (
                isinstance(func, torch._ops.HigherOrderOperator)
                and func.name() == "invoke_subgraph"
            ):
                hc_log.debug(
                    "Fake tensor cache failed: identifier = %s, reason = %s",
                    args[1],
                    e.reason,
                )
            FakeTensorMode.cache_bypasses[e.reason] += 1

        if key is None:
            # Do this dispatch outside the above except handler so if it
            # generates its own exception there won't be a __context__ caused by
            # the caching mechanism.

            return self._dispatch_impl(func, types, args, kwargs)

        if state is None:
            raise AssertionError("state must not be None after cache key generation")
        if state.cache_on_shape_env():
            if state.shape_env is None:
                raise AssertionError(
                    "state.shape_env must not be None when caching on shape_env"
                )
            cache = state.shape_env.fake_tensor_cache
            set_cache_key = _set_cache_key_for_shape_env
        else:
            cache = FakeTensorMode.cache
            set_cache_key = _set_cache_key
        entry = cache.get(key, None)

        if entry is not None:
            if isinstance(entry, _DispatchCacheBypassEntry):
                # This represents a negative cache entry - we already saw that the
                # output is uncachable. Compute it from first principals.
                FakeTensorMode.cache_bypasses[entry.reason] += 1

                return self._dispatch_impl(func, types, args, kwargs)

            # We have a cache entry.

            output = self._output_from_cache_entry(state, entry, key, func, args)
            FakeTensorMode.cache_hits += 1
            if self.cache_crosscheck_enabled:
                # For debugging / testing: Validate that the output synthesized
                # from the cache matches the output created by normal dispatch.
                with disable_fake_tensor_cache(self):
                    self._crosscheck_cache_output(output, func, types, args, kwargs)
            return output

        # We don't have a cache entry.

        output = self._dispatch_impl(func, types, args, kwargs)

        try:
            entry = self._make_cache_entry(state, key, func, args, kwargs, output)
        except _BypassDispatchCache as e:
            # We ran "extra" checks on the cache key and determined that it's no
            # good. Record the reason and mark it so we don't bother validating
            # again.
            if (
                isinstance(func, torch._ops.HigherOrderOperator)
                and func.name() == "invoke_subgraph"
            ):
                hc_log.debug(
                    "Fake tensor cache failed: identifier = %s, reason = %s",
                    args[1],
                    e.reason,
                )
            FakeTensorMode.cache_bypasses[e.reason] += 1
            set_cache_key(cache, key, _DispatchCacheBypassEntry(e.reason))
            return output

        set_cache_key(cache, key, entry)
        FakeTensorMode.cache_misses += 1
        return output