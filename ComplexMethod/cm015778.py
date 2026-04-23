def test_sac_deferred(self):
        # This test is in a bit of a weird state, it needs compositional compile API
        # so that we can defer inlining for up until AOTAutograd stage 1.
        # Then we should be inlined by stage 2. But we can't do that today.

        cp_decorated, cp_function = get_local_mapped_functions(self.mesh)
        bs = 8 * 1
        dim1 = 128
        dim2 = dim1 * 4
        nheads = 16
        seq_len = 16

        from torch._dynamo.testing import AotEagerAndRecordGraphs, normalize_gm

        backend = AotEagerAndRecordGraphs()

        model = create_model(
            cp_decorated, nheads, dim1, dim2, sac_policy=save_scalar_muls
        ).to(torch.bfloat16)
        inputs = (
            torch.randn(bs, seq_len, dim1, requires_grad=True, dtype=torch.bfloat16),
        )
        try:
            with enable_local_map_wrapping():
                out = torch.compile(model, backend=backend)(*inputs)
            out.sum().backward()
        except AttributeError as e:
            # TODO: get rid of this when we can install as a subgraph
            self.assertTrue(
                "module 'torch._higher_order_ops.local_map' has no attribute 'call_local_map'"
                in str(e)
            )

        model = create_model(
            cp_function, nheads, dim1, dim2, sac_policy=save_scalar_muls
        ).to(torch.bfloat16)
        inputs = (
            torch.randn(bs, seq_len, dim1, requires_grad=True, dtype=torch.bfloat16),
        )
        try:
            with enable_local_map_wrapping():
                out = torch.compile(model, backend=backend)(*inputs)
            out.sum().backward()
        except AttributeError as e:
            # TODO: get rid of this when we can install as a subgraph
            self.assertTrue(
                "module 'torch._higher_order_ops.local_map' has no attribute 'call_local_map'"
                in str(e)
            )

        # TODO: re-enable tests on backward when we can install as a subgraph
        if not TEST_WITH_CROSSREF:
            self.assertEqual(len(backend.graphs), 2)
            self.assertEqual(
                normalize_gm(backend.graphs[0].print_readable(print_output=False)),
                normalize_gm(backend.graphs[1].print_readable(print_output=False)),
            )
            self.assertEqual(
                normalize_gm(backend.fw_graphs[0].print_readable(print_output=False)),
                normalize_gm(backend.fw_graphs[1].print_readable(print_output=False)),
            )
            # self.assertEqual(
            #     normalize_gm(backend.bw_graphs[0].print_readable(print_output=False)),
            #     normalize_gm(backend.bw_graphs[1].print_readable(print_output=False)),
            # )
            self.assertEqual(
                len(
                    backend.graphs[0].graph.find_nodes(
                        op="call_function",
                        target=torch._higher_order_ops.wrap.tag_activation_checkpoint,
                    )
                ),
                1,
            )
            # TODO: add joint to the testing compile backend
            fw_outs = {
                n.name
                for n in backend.fw_graphs[0].graph.find_nodes(op="output")[0].args[0]
            }
            # bw_ins = {
            #     n.name for n in backend.bw_graphs[0].graph.find_nodes(op="placeholder")
            # }
            for node in backend.fw_graphs[0].graph.nodes:
                if "recompute" in node.meta:
                    expected = save_scalar_muls(None, node.target, None, None)
                    actual = node.meta["recompute"]
                    self.assertEqual(expected, actual)
                    if actual == torch.utils.checkpoint.CheckpointPolicy.MUST_SAVE:
                        self.assertTrue(node.name in fw_outs)