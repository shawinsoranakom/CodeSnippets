def test_force_save_effectful_ops(self):
        """Test that effectful op outputs are saved, not recomputed.

        This test traces a function with a with_effects node and verifies
        that the getitem outputs are marked MUST_SAVE.
        """
        from torch._functorch.partitioners import (
            CheckpointPolicy,
            force_save_effectful_ops,
        )
        from torch._higher_order_ops.effects import _register_effectful_op, with_effects
        from torch._library.effects import EffectType

        @torch.library.custom_op("test::effectful_op", mutates_args=())
        def effectful_op(x: torch.Tensor) -> torch.Tensor:
            return x * 2

        @effectful_op.register_fake
        def _(x: torch.Tensor) -> torch.Tensor:
            return torch.empty_like(x)

        handle = _register_effectful_op(effectful_op, EffectType.ORDERED)

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
            def fn(x, weight):
                a = torch.ops.test.effectful_op(x)
                return a.sum() * weight

            x = torch.randn(4, 4)
            weight = torch.randn(4, 4)
            fn(x, weight)

            force_save_effectful_ops(gm)

            with_effects_nodes = [
                n
                for n in gm.graph.nodes
                if n.op == "call_function" and n.target == with_effects
            ]
            self.assertEqual(
                len(with_effects_nodes), 1, "should have one with_effects node"
            )

            getitem_nodes = [
                n
                for n in gm.graph.nodes
                if n.op == "call_function"
                and n.target == operator.getitem
                and n.args[0] == with_effects_nodes[0]
            ]

            def is_must_save(node):
                return node.meta.get("recompute") == CheckpointPolicy.MUST_SAVE

            must_save_count = sum(1 for n in getitem_nodes if is_must_save(n))
            self.assertEqual(
                must_save_count,
                2,
                f"2 items should be MUST_SAVE, got {must_save_count}",
            )
            self.assertEqual(
                len(getitem_nodes),
                must_save_count,
                "all getitem nodes should be MUST_SAVE",
            )
        finally:
            handle.destroy()