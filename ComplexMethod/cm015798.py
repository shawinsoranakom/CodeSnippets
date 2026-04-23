def test_with_effects_reinplace(self):
        """Test that the reinplace pass correctly handles with_effects wrapped ops.

        When an effectful op is wrapped with with_effects, the reinplace pass should:
        1. Find the inner op in the inplaceable_ops registry
        2. Correctly compute the mutated arg indices (offset by 2 for token and op)
        3. Convert functional -> inplace when safe
        4. Replace getitem nodes that extract results with input tensors
        """
        from torch._higher_order_ops.effects import with_effects
        from torch._inductor.fx_passes.reinplace import inplaceable_ops, InplaceableOp

        # Define a simple effectful op pair (functional and inplace)
        @torch.library.custom_op("_test_effects::my_add", mutates_args=())
        def my_add_functional(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
            return x + y

        @my_add_functional.register_fake
        def _(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
            return torch.empty_like(x)

        @torch.library.custom_op("_test_effects::my_add_", mutates_args={"x"})
        def my_add_inplace(x: torch.Tensor, y: torch.Tensor) -> None:
            x.add_(y)

        @my_add_inplace.register_fake
        def _(x: torch.Tensor, y: torch.Tensor) -> None:
            pass

        # Register the functional -> inplace mapping
        inplaceable_ops[my_add_functional._opoverload] = InplaceableOp(
            my_add_inplace._opoverload,
            0,  # First tensor arg (x) is mutated
        )

        try:

            def f(a, b):
                # Create tensors from ops (not placeholders) so can_inplace works
                x = a.clone()
                y = b.clone()
                token = torch.ops.aten._make_dep_token()
                result = with_effects(token, my_add_functional._opoverload, x, y)
                # with_effects returns (new_token, result_tensor)
                return result[1]

            a = torch.randn(3, device=device)
            b = torch.randn(3, device=device)

            gm = make_fx(f, tracing_mode="fake")(a, b)

            # Find the with_effects node before reinplace
            with_effects_nodes_before = [
                n
                for n in gm.graph.nodes
                if n.target is torch.ops.higher_order.with_effects
            ]
            self.assertEqual(len(with_effects_nodes_before), 1)

            # The inner op should be the functional version
            inner_op_before = with_effects_nodes_before[0].args[1]
            self.assertEqual(inner_op_before, my_add_functional._opoverload)

            # Count getitem nodes before reinplace
            getitem_nodes_before = [
                n for n in gm.graph.nodes if n.target is operator.getitem
            ]
            self.assertGreater(len(getitem_nodes_before), 0)

            # Run reinplace pass
            reinplace_inplaceable_ops_core(gm.graph)

            # Find the with_effects node after reinplace
            with_effects_nodes_after = [
                n
                for n in gm.graph.nodes
                if n.target is torch.ops.higher_order.with_effects
            ]
            self.assertEqual(len(with_effects_nodes_after), 1)

            # The inner op should now be the inplace version
            inner_op_after = with_effects_nodes_after[0].args[1]
            self.assertEqual(inner_op_after, my_add_inplace._opoverload)

            # Verify getitem nodes for result extraction are cleaned up
            # (getitem[i] for i >= 1 on with_effects should be removed or replaced)
            getitem_nodes_after = [
                n
                for n in gm.graph.nodes
                if n.target is operator.getitem
                and n.args[0] is with_effects_nodes_after[0]
                and n.args[1] >= 1
            ]
            self.assertEqual(
                len(getitem_nodes_after),
                0,
                "getitem nodes extracting result should be cleaned up",
            )

        finally:
            if my_add_functional._opoverload in inplaceable_ops:
                del inplaceable_ops[my_add_functional._opoverload]