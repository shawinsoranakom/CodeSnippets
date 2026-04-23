def cache_hit_post_compile(
        graph: CompiledFxGraph,
        cache_info: dict[str, Any],
        constants: CompiledFxGraphConstants,
    ) -> tuple[CompiledFxGraph | None, dict[str, Any]]:
        """
        Cache specific post compile steps that need to run if we find a graph in the cache
        This includes putting bundled triton artifacts in the right place,
        reloading the PyCodeCache artifact, etc.

        These don't always happen (i.e. on a cache miss, so they are in a separate function from
        CompiledFxGraph.post_compile)
        """
        if bundle := graph._triton_bundle:
            triton_bundler_meta = TritonBundler.read_and_emit(bundle)
            if (meta := triton_bundler_meta) is not None:
                cache_info["triton_bundler_meta"] = str(meta)
                CompileEventLogger.try_add_pt2_compile(
                    "inductor_compile", cached_kernel_names=meta.cached_kernel_names
                )
                CompileEventLogger.try_add_pt2_compile(
                    "AOTAutogradCache.inductor_load",
                    cached_kernel_names=meta.cached_kernel_names,
                )
                if len(meta.cached_kernel_names) > 0:
                    CompileEventLogger.try_(
                        CompileEventLogger.increment_toplevel, "num_triton_bundles"
                    )

        try:
            artifact_path = graph.after_deserialization(constants)

            from .graph import GraphLowering

            # This is used by tests to check the output for specific details.
            if GraphLowering.save_output_code is not None:
                GraphLowering.save_output_code(graph.source_code)

        except OSError:
            # Not expected, but in case the PyCodeCache entry is removed from
            # underneath us, treat it as a cache miss and recompile.
            return None, cache_info

        inductor_meta = autotune_cache.inductor_meta_from_config()
        code = graph.source_code
        AutotuneCacheBundler.begin_compile(inductor_meta, code=code)

        # Increment the cached metrics/counters by the amounts recorded when the FX
        # graph was compiled for this cache entry. Pretending these counters
        # were incremented normally is useful for testing with the cache enabled.
        metrics.CachedMetricsHelper.apply_deltas(graph.metrics_deltas)
        counters["inductor"] += graph.counter_deltas

        output_code_log.debug("Output code: \n%s", code)
        output_code_log.debug("Output code written to: %s", artifact_path)
        # On cache hit, use artifact path as filename
        trace_structured(
            "artifact",
            metadata_fn=lambda: {
                "name": "fx_graph_runnable",
                "encoding": "string",
            },
            payload_fn=lambda: graph.runnable_graph_str,
        )
        trace_structured(
            "inductor_post_grad_graph",
            payload_fn=lambda: graph.inductor_post_grad_graph_str,
        )
        trace_structured(
            "inductor_output_code",
            lambda: {
                "filename": artifact_path,
                "file_path": os.path.abspath(artifact_path),
            },
            payload_fn=lambda: code,
        )
        trace_structured(
            "artifact",
            metadata_fn=lambda: {
                "name": "inductor_provenance_tracking_node_mappings",
                "encoding": "json",
            },
            payload_fn=lambda: graph.inductor_provenance_mapping_str,
        )
        trace_structured(
            "artifact",
            metadata_fn=lambda: {
                "name": "inductor_provenance_tracking_kernel_stack_traces",
                "encoding": "json",
            },
            payload_fn=lambda: graph.inductor_provenance_stack_traces_str,
        )
        if (
            get_metrics_context().in_progress()
            and graph.inductor_provenance_stack_traces_str
        ):
            get_metrics_context().add_to_set(
                "inductor_provenance", graph.inductor_provenance_stack_traces_str
            )
        return graph, cache_info