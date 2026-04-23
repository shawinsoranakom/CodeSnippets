def test_force_save_effectful_ops_nested_tuple(self):
        """Test that effectful ops returning tuples have all tensor outputs marked MUST_SAVE.

        This test creates a custom op that returns a tuple, registers it as effectful,
        and verifies that all tensor getitems are marked MUST_SAVE after tracing.
        """
        from torch._functorch.partitioners import (
            CheckpointPolicy,
            force_save_effectful_ops,
        )
        from torch._higher_order_ops.effects import _register_effectful_op, with_effects
        from torch._library.effects import EffectType

        @torch.library.custom_op("test::effectful_tuple_op", mutates_args=())
        def effectful_tuple_op(x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
            return x * 2, x + 1

        @effectful_tuple_op.register_fake
        def _(x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
            return torch.empty_like(x), torch.empty_like(x)

        handle = _register_effectful_op(effectful_tuple_op, EffectType.ORDERED)

        try:
            gm = None

            def graph_capture_backend(graph_module, example_inputs):
                """Custom backend that captures the graph before passing to inductor."""
                nonlocal gm

                from torch._inductor.compile_fx import compile_fx, compile_fx_inner

                def log_and_compile(graph_module, example_inputs, **kwargs):
                    nonlocal gm
                    gm = graph_module
                    return compile_fx_inner(graph_module, example_inputs, **kwargs)

                return compile_fx(
                    graph_module, example_inputs, inner_compile=log_and_compile
                )

            @torch.compile(backend=graph_capture_backend)
            def fn(x):
                a, b = torch.ops.test.effectful_tuple_op(x)
                return a.sum() + b.sum()

            x = torch.randn(4, 4)
            fn(x)

            with_effects_node = None
            for node in gm.graph.nodes:
                if node.op == "call_function" and node.target == with_effects:
                    with_effects_node = node
                    break
            self.assertIsNotNone(with_effects_node, "should have a with_effects node")

            getitem_nodes = [
                n
                for n in gm.graph.nodes
                if n.op == "call_function"
                and n.target == operator.getitem
                and n.args[0] == with_effects_node
            ]

            force_save_effectful_ops(gm)

            def is_must_save(node):
                return node.meta.get("recompute") == CheckpointPolicy.MUST_SAVE

            tensor_getitem_count = 0
            must_save_count = 0
            for node in getitem_nodes:
                val = node.meta.get("val")
                if isinstance(val, torch.Tensor):
                    tensor_getitem_count += 1
                    if is_must_save(node):
                        must_save_count += 1

            self.assertEqual(
                tensor_getitem_count,
                3,
                f"expected 3 getitems, got {tensor_getitem_count}",
            )
            self.assertEqual(
                must_save_count,
                tensor_getitem_count,
                f"all {tensor_getitem_count} tensor getitems should be MUST_SAVE, got {must_save_count}",
            )
        finally:
            handle.destroy()