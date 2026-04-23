def _lookup_graph(
        key: str,
        example_inputs: Sequence[InputType],
        local: bool,
        remote_cache: RemoteCache[JsonDataTy] | None,
        constants: CompiledFxGraphConstants,
        evaluate_guards: Callable[[str, list[int] | list[torch.SymInt]], bool]
        | None = None,
    ) -> tuple[CompiledFxGraph | None, dict[str, Any]]:
        """
        Lookup a compiled graph in the cache by key. On a hit, return the
        deserialized CompiledFxGraph object. On a miss, return None.
        `constants` tracks a list of constants, or a way to obtain the list of constants
        associated with a given cache entry
        `evaluate_guards` allows AOTAutogradCache and other callers to customize
        what constitutes a guard success. Normally, a guard hit happens if
        `shape_env.evaluate_guards_expression` returns True.
        """
        shape_env = FxGraphCache._get_shape_env()
        assert shape_env is not None

        symints = FxGraphCache._filter_backed_symints(example_inputs)
        hints = [guarding_hint_or_throw(s) for s in symints]

        # If this config is turned on, everything is a guard hit and we check nothing
        if config.unsafe_skip_cache_dynamic_shape_guards:
            # This also makes it so we don't add anything to the dynamic
            # shape environment
            evaluate_guards = lambda x, y: True  # noqa: E731

        if evaluate_guards is None:
            evaluate_guards = shape_env.evaluate_guards_expression

        cache_info: dict[str, Any] = dict()

        # Use the find_graph_for_key method to find a graph for the given key
        graph, pickled_content, guard_info = FxGraphCache.find_guarded_entry(
            key, local, remote_cache, evaluate_guards, hints
        )
        cache_info.update(guard_info)
        if graph is None:
            return None, cache_info

        # Validate extern_libs (e.g. libdevice) match the current env.
        if graph.extern_libs_key is not None:
            try:
                backend = torch.utils._triton.triton_backend()
                current = torch.utils._triton._extern_libs_key(backend)
            except Exception:
                current = None
            if current != graph.extern_libs_key:
                cache_info["cache_status_detailed"] = "guard_miss"
                return None, cache_info

        if pickled_content is not None:
            CacheArtifactManager.record_artifact(
                InductorCacheArtifact.type(), key, pickled_content
            )

        # Now re-evaluate with the symints to add any guards to the current env.
        if graph.guards_expr:
            check = bool(evaluate_guards(graph.guards_expr, symints))
            assert check is True
            log.debug(
                "fx graph cache key %s post-load guards: %s", key, shape_env.guards
            )

        return FxGraphCache.cache_hit_post_compile(graph, cache_info, constants)