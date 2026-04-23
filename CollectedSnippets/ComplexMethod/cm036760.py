def test_pattern_matcher_replaces_with_helion_hop(self):
        def raw_silu_mul(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
            M, N = x.size()
            out = torch.empty_like(x)
            for tile_m, tile_n in hl.tile([M, N]):
                out[tile_m, tile_n] = (
                    torch.nn.functional.silu(x[tile_m, tile_n]) * y[tile_m, tile_n]
                )
            return out

        with _helion_mock_context():
            wrapper = HelionKernelWrapper(
                raw_kernel_func=raw_silu_mul,
                op_name="test_pm_silu_mul",
                fake_impl=lambda *a, **kw: None,
                config_picker=lambda args, keys: "default",
            )

            def pattern(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
                return torch.nn.functional.silu(x) * y

            def replacement(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
                return wrapper(x, y)

            inputs = [torch.randn(8, 16), torch.randn(8, 16)]

            pm_pass = PatternMatcherPass(pass_name="test_helion_replacement")
            register_replacement(pattern, replacement, inputs, fwd_only, pm_pass)

            def model(x, y):
                return torch.nn.functional.silu(x) * y

            decompositions = select_decomp_table()
            input_x = torch.randn(8, 16)
            input_y = torch.randn(8, 16)
            gm = make_fx(model, decompositions, tracing_mode="symbolic")(
                input_x, input_y
            )

            def count_hop_nodes(graph):
                return sum(
                    1
                    for n in graph.nodes
                    if n.op == "call_function"
                    and n.target is helion_kernel_wrapper_mutation
                )

            assert count_hop_nodes(gm.graph) == 0

            match_count = pm_pass.apply(gm.graph)
            gm.graph.lint()
            gm.recompile()

            assert match_count == 1
            assert count_hop_nodes(gm.graph) == 1

            hop_node = next(
                n
                for n in gm.graph.nodes
                if n.op == "call_function"
                and n.target is helion_kernel_wrapper_mutation
            )

            # raw_silu_mul returns empty_like(x), so output shape == input shape
            for val in hop_node.meta["val"]:
                assert all(isinstance(s, torch.SymInt) for s in val.shape)

            input_node = next(n for n in gm.graph.nodes if n.op == "placeholder")
            input_shape = input_node.meta["val"].shape
            output_shape = hop_node.meta["val"][0].shape
            assert len(output_shape) == len(input_shape)
            for out_s, in_s in zip(output_shape, input_shape):
                assert out_s == in_s