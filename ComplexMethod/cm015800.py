def test_with_effects_reinplace_list_arg(self):
        """Test reinplace pass with list arguments in with_effects wrapped ops.

        This tests the case where the mutated argument is a list of tensors,
        similar to wait_tensors operations that take a list of tensors to wait on.
        """
        from torch._higher_order_ops.effects import with_effects
        from torch._inductor.fx_passes.reinplace import inplaceable_ops, InplaceableOp

        # Define an op that takes a list of tensors (functional version)
        @torch.library.custom_op("_test_effects::my_wait", mutates_args=())
        def my_wait_functional(
            tensors: list[torch.Tensor],
        ) -> list[torch.Tensor]:
            return [t.clone() for t in tensors]

        @my_wait_functional.register_fake
        def _(tensors: list[torch.Tensor]) -> list[torch.Tensor]:
            return [torch.empty_like(t) for t in tensors]

        # Define inplace version that mutates the list of tensors
        @torch.library.custom_op("_test_effects::my_wait_", mutates_args={"tensors"})
        def my_wait_inplace(tensors: list[torch.Tensor]) -> None:
            pass  # In reality would wait on async ops

        @my_wait_inplace.register_fake
        def _(tensors: list[torch.Tensor]) -> None:
            pass

        # Register the functional -> inplace mapping
        inplaceable_ops[my_wait_functional._opoverload] = InplaceableOp(
            my_wait_inplace._opoverload,
            0,  # First arg (tensors list) is mutated
        )

        try:

            def f(a, b, c):
                # Create tensors from ops (not placeholders) so can_inplace works
                x = a.clone()
                y = b.clone()
                z = c.clone()
                token = torch.ops.aten._make_dep_token()
                result = with_effects(token, my_wait_functional._opoverload, [x, y, z])
                # Access individual results from the list
                out = result[1]
                return out[0], out[1], out[2]

            a = torch.randn(3, device=device)
            b = torch.randn(3, device=device)
            c = torch.randn(3, device=device)

            gm = make_fx(f, tracing_mode="fake")(a, b, c)

            # Find the with_effects node before reinplace
            with_effects_nodes_before = [
                n
                for n in gm.graph.nodes
                if n.target is torch.ops.higher_order.with_effects
            ]
            self.assertEqual(len(with_effects_nodes_before), 1)

            # The inner op should be the functional version
            inner_op_before = with_effects_nodes_before[0].args[1]
            self.assertEqual(inner_op_before, my_wait_functional._opoverload)

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
            self.assertEqual(inner_op_after, my_wait_inplace._opoverload)

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
                "getitem nodes extracting result list should be cleaned up",
            )

        finally:
            if my_wait_functional._opoverload in inplaceable_ops:
                del inplaceable_ops[my_wait_functional._opoverload]