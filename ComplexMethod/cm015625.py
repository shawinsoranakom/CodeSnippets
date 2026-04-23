def _run_with_override(self, device, override_config, default_backend="eager"):
        from torch._dynamo.graph_id_filter import (
            _create_backend_router,
            get_backend_override_for_compile_id,
        )

        torch._dynamo.reset()
        # Clear the router cache to ensure fresh routers for each test
        _create_backend_router.cache_clear()
        self._backends_called.clear()
        original_get_override = get_backend_override_for_compile_id

        # Pre-parse the config to build a mapping of graph_id -> backend_str
        # by using the same parsing logic but extracting the original strings
        backend_str_map: dict[int, str] = {}
        if override_config:
            for rule_str in override_config.split(";"):
                rule_str = rule_str.strip()
                if not rule_str or ":" not in rule_str:
                    continue
                colon_idx = rule_str.find(":")
                filter_str = rule_str[:colon_idx].strip()
                backend_str = rule_str[colon_idx + 1 :].strip()
                # Parse the filter to extract graph IDs
                from torch._dynamo.graph_id_filter import GraphIdFilter

                gf = GraphIdFilter(filter_str)
                # Store the backend_str for any graph that matches this filter
                for graph_id in range(100):  # Check first 100 graphs
                    if graph_id in gf and graph_id not in backend_str_map:
                        backend_str_map[graph_id] = backend_str

        def tracking_get_override(compile_id, config_str):
            result = original_get_override(compile_id, config_str)
            if result is not None:
                graph_id = compile_id.frame_id
                if graph_id in backend_str_map:
                    self._backends_called.append(backend_str_map[graph_id])
            return result

        with (
            patch.object(
                torch._dynamo.config, "debug_backend_override", override_config
            ),
            patch(
                "torch._dynamo.output_graph.get_backend_override_for_compile_id",
                tracking_get_override,
            ),
        ):
            compiled_fn = torch.compile(self._fn_with_4_graphs, backend=default_backend)
            compiled_fn(torch.randn(10, device=device))

        return self._backends_called.copy()