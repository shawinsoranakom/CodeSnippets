def compile(
        self,
        graph: fx.GraphModule,
        example_inputs: list[Any],
        additional_inductor_config: dict[str, Any],
        compilation_config: CompilationConfig,
        compile_range: Range,
        graph_index: int = 0,
        num_graphs: int = 1,
        is_encoder: bool = False,
    ) -> Any:
        if graph_index == 0:
            # before compiling the first graph, record the start time
            global compilation_start_time
            compilation_start_time = time.perf_counter()

        compilation_counter.num_backend_compilations += 1

        compiled_graph = None

        # try to load from the cache
        compiled_graph = self.load(graph, example_inputs, graph_index, compile_range)
        if compiled_graph is not None:
            if graph_index == num_graphs - 1:
                # after loading the last graph for this shape, record the time.
                # there can be multiple graphs due to piecewise compilation.
                elapsed = time.perf_counter() - compilation_start_time
                logger.info_once(
                    "Directly load the compiled graph(s) for compile range %s "
                    "from the cache, took %.3f s",
                    str(compile_range),
                    elapsed,
                )
            return compiled_graph

        # no compiler cached the graph, or the cache is disabled,
        # we need to compile it
        if isinstance(self.compiler, InductorAdaptor):
            # Let compile_fx generate a key for us
            maybe_key = None
        else:
            maybe_key = "artifact_compile_range_"
            maybe_key += f"{compile_range.start}_{compile_range.end}"
            maybe_key += f"_subgraph_{graph_index}"
        with self.compile_context(compile_range):
            # There is a compilation time optimization here.
            #
            # If the (input metadata, graph, compiler config) are the same, then
            # we want to avoid compiling the same artifact again. If we didn't
            # do this optimization, the backend compilation (InductorAdaptor or
            # InductorStandaloneAdaptor)
            # is able to cache hit and produce an artifact faster if it was
            # already created, but it is still a duplicate artifact that
            # requires unnecessary things e.g. disk IO.
            #
            # The optimization is: If the backend compilation cache hits,
            # then do an early return from the backend compilation and look up
            # which of the previous in-memory artifacts we created to reuse.
            #
            # We implemented this by monkey-patching torch (torch does not
            # easily expose the cache_key function), but in the future torch
            # should expose the cache_key function that we can just call
            # directly before invoking backend compilation.
            cache_key = None
            orig = torch._functorch._aot_autograd.autograd_cache.autograd_cache_key

            def autograd_cache_key(*args, **kwargs):
                result = orig(*args, **kwargs)
                if result is None:
                    return None
                nonlocal cache_key
                cache_key = result[0]
                if cache_key in self.loaded_artifacts:
                    raise StopCompiling()
                return result

            from unittest.mock import patch

            with (
                # Graphs that are isometric (different node names but same
                # structure) should be treated as the same.
                torch._functorch.config.patch(autograd_cache_normalize_inputs=True),
                patch(
                    "torch._functorch._aot_autograd.autograd_cache.autograd_cache_key",
                    autograd_cache_key,
                ),
            ):
                try:
                    compiled_graph, handle = self.compiler.compile(
                        graph,
                        example_inputs,
                        additional_inductor_config,
                        compile_range,
                        maybe_key,
                    )
                except StopCompiling:
                    assert cache_key is not None
                    return self.loaded_artifacts[cache_key]
            if cache_key is not None and compiled_graph is not None:
                self.loaded_artifacts[cache_key] = compiled_graph

        assert compiled_graph is not None, "Failed to compile the graph"

        # store the artifact in the cache
        if is_compile_cache_enabled(additional_inductor_config) and handle is not None:
            self.cache[(compile_range, graph_index, self.compiler.name)] = {
                "graph_handle": handle,
                "cache_key": cache_key,
            }
            compilation_counter.num_cache_entries_updated += 1
            self.is_cache_updated = True
            if graph_index == 0:
                # adds some info logging for the first graph
                logger.info_once(
                    "Cache the graph of compile range %s for later use",
                    str(compile_range),
                )
            logger.debug_once(
                "Store the %s-th graph for compile range%s from %s via handle %s",
                graph_index,
                str(compile_range),
                self.compiler.name,
                handle,
            )

        # after compiling the last graph, record the end time
        if graph_index == num_graphs - 1:
            elapsed = time.perf_counter() - compilation_start_time
            logger.info_once(
                "Compiling a graph for compile range %s takes %.2f s",
                str(compile_range),
                elapsed,
            )

        return compiled_graph