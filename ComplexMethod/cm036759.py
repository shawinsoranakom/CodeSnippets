def test_make_fx_symbolic(self):
        def raw_add_scale(
            x: torch.Tensor, y: torch.Tensor, scale: float
        ) -> tuple[torch.Tensor, int, torch.Tensor]:
            out_x = torch.empty_like(x)
            out_y = torch.empty_like(x)
            for tile in hl.tile(x.size()):
                out_x[tile] = x[tile] + y[tile] * scale
                out_y[tile] = out_x[tile] * 2.0
            return out_x, 42, out_y

        input_x = torch.randn(7, 13)
        input_y = torch.randn(7, 13)
        scale = 0.5

        with _helion_mock_context():
            wrapper = HelionKernelWrapper(
                raw_kernel_func=raw_add_scale,
                op_name="test_make_fx",
                fake_impl=lambda *a, **kw: None,
                config_picker=lambda args, keys: "default",
            )

            def fn(x, y):
                return wrapper(x, y, scale)

            gm = make_fx(fn, tracing_mode="symbolic")(input_x, input_y)

        hop_nodes = [
            n
            for n in gm.graph.nodes
            if n.op == "call_function" and n.target is helion_kernel_wrapper_mutation
        ]
        assert len(hop_nodes) == 1
        node = hop_nodes[0]

        assert node.kwargs["constant_args"]["scale"] == scale
        assert set(node.kwargs["tensor_args"]) == {"x", "y"}

        specs = node.kwargs["output_spec"]["leaf_specs"]
        tensor_specs = [s for s in specs if s["type"] == "tensor"]
        scalar_specs = [s for s in specs if s["type"] == "scalar"]
        assert len(tensor_specs) == 2
        assert len(scalar_specs) == 1

        for spec in tensor_specs:
            assert spec["dtype"] == input_x.dtype

        assert scalar_specs[0]["scalar_value"] == 42

        for val in node.meta["val"]:
            assert all(isinstance(s, torch.SymInt) for s in val.shape)

        # Both out_x and out_y are empty_like(x), so output shapes == input shape
        input_node = next(n for n in gm.graph.nodes if n.op == "placeholder")
        input_shape = input_node.meta["val"].shape
        for val in node.meta["val"]:
            assert len(val.shape) == len(input_shape)
            for out_s, in_s in zip(val.shape, input_shape):
                assert out_s == in_s