def _save_graph(
        key: str,
        compiled_graph: OutputCode,
        example_inputs: Sequence[InputType],
        local: bool,
        remote_cache: RemoteCache[JsonDataTy] | None,
    ) -> None:
        """
        Store a serialized CompiledFxGraph on disk.
        """
        from .compile_fx import CompiledFxGraph

        assert isinstance(compiled_graph, CompiledFxGraph), (
            f"serialization for {type(compiled_graph)} NYI"
        )

        # Before serializing, compute the guard expression that will be used to
        # ensure that a CompiledFxGraph is valid when loaded from the cache. It's
        # sufficient to consider only the SymInt args to the fx graph since the
        # Tensor shapes are already captured in the hash for the cache key. Any
        # Tensor arg with a symbolic shape will have a SymInt arg for the graph.
        shape_env = FxGraphCache._get_shape_env()
        assert shape_env is not None
        symints = FxGraphCache._filter_backed_symints(example_inputs)
        guards = shape_env.get_pruned_guards(symints)
        compiled_graph.guards_expr = shape_env.produce_guards_expression(
            placeholders=symints, guards=guards
        )
        try:
            backend = torch.utils._triton.triton_backend()
            compiled_graph.extern_libs_key = torch.utils._triton._extern_libs_key(
                backend
            )
        except Exception:
            pass
        disk_compiled_graph = copy(compiled_graph)
        disk_compiled_graph.prepare_for_serialization()

        try:
            content = pickle.dumps(disk_compiled_graph)
        except Exception:
            log.warning(
                "fx graph cache unable to serialize compiled graph", exc_info=True
            )
            counters["inductor"]["fxgraph_cache_pickle_error"] += 1
            return

        try:
            CacheArtifactManager.record_artifact(
                InductorCacheArtifact.type(), key, content
            )
            if local:
                FxGraphCache._write_to_local_cache(key, content)

            if remote_cache:
                time_taken_ms = int((disk_compiled_graph._time_taken_ns or 0) // 1e6)
                cache_data: JsonDataTy = {
                    "data": base64.b64encode(content).decode("ascii"),
                    "time_taken_ms": time_taken_ms,
                }
                remote_cache.put(key, cache_data)
        except Exception:
            log.warning("fx graph unable to write to cache", exc_info=True)
            counters["inductor"]["fxgraph_cache_write_error"] += 1