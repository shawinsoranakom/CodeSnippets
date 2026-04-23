def test_with_effects_reinplace_multiple_mutated_args(self):
        """Test reinplace pass with multiple mutated args in with_effects wrapped ops.

        This tests the case where an effectful op mutates multiple tensors,
        such as collective operations that update multiple output buffers.
        """
        from torch._higher_order_ops.effects import with_effects
        from torch._inductor.fx_passes.reinplace import inplaceable_ops, InplaceableOp

        # Define an op that returns two tensors (functional version)
        @torch.library.custom_op("_test_effects::my_swap", mutates_args=())
        def my_swap_functional(
            x: torch.Tensor, y: torch.Tensor
        ) -> tuple[torch.Tensor, torch.Tensor]:
            # Swap values between x and y
            return y.clone(), x.clone()

        @my_swap_functional.register_fake
        def _(x: torch.Tensor, y: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
            return torch.empty_like(x), torch.empty_like(y)

        # Define inplace version that mutates both x and y
        @torch.library.custom_op("_test_effects::my_swap_", mutates_args={"x", "y"})
        def my_swap_inplace(x: torch.Tensor, y: torch.Tensor) -> None:
            tmp = x.clone()
            x.copy_(y)
            y.copy_(tmp)

        @my_swap_inplace.register_fake
        def _(x: torch.Tensor, y: torch.Tensor) -> None:
            pass

        # Register the functional -> inplace mapping with multiple mutated args
        inplaceable_ops[my_swap_functional._opoverload] = InplaceableOp(
            my_swap_inplace._opoverload,
            (0, 1),  # Both x (arg 0) and y (arg 1) are mutated
        )

        try:

            def f(a, b):
                # Create tensors from ops (not placeholders) so can_inplace works
                x = a.clone()
                y = b.clone()
                token = torch.ops.aten._make_dep_token()
                result = with_effects(token, my_swap_functional._opoverload, x, y)
                # with_effects returns (new_token, (tensor1, tensor2))
                # Access both results
                out = result[1]
                return out[0], out[1]

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
            self.assertEqual(inner_op_before, my_swap_functional._opoverload)

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
            self.assertEqual(inner_op_after, my_swap_inplace._opoverload)

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
                "getitem nodes extracting result tuple should be cleaned up",
            )

        finally:
            if my_swap_functional._opoverload in inplaceable_ops:
                del inplaceable_ops[my_swap_functional._opoverload]