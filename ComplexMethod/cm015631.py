def test_control_deps_wrapping_synchronize_event(self) -> None:
        """Test that synchronize_event threads recorded ops' values through.

        After record_event wraps ops in control_deps and produces getitem
        pass-throughs, synchronize_event must also thread those through so
        that subsequent consumers depend on the synchronize.
        """

        def fn(x) -> torch.Tensor:
            e = torch.Event()
            y = x + 1
            e.record()
            e.synchronize()
            # z uses y which was produced before the record — its value must
            # be threaded through both record and synchronize control_deps.
            z = y * 2
            return z

        inp = (torch.ones(2, 2, device="cuda"),)
        # Patch out wrapping so we get the raw graph to manually wrap below.
        with patch(
            "torch._functorch._aot_autograd.graph_capture.wrap_all_sync_nodes_with_control_deps"
        ):
            (
                _,
                _,
                fw_graphs,
                _,
            ) = extract_graph(fn, *inp)

        gm = fw_graphs[0]
        graph = gm.graph

        import operator

        from torch._functorch._aot_autograd.streams import (
            set_stream,
            wrap_all_sync_nodes_with_control_deps,
        )
        from torch._inductor.fx_passes.control_dependencies import control_deps

        # extract_graph doesn't annotate streams, so set stream metadata on
        # compute nodes to match the record_event's stream index.
        record_node = next(
            n
            for n in graph.nodes
            if n.op == "call_function"
            and n.target is torch.ops.streams.record_event.default
        )
        stream_idx = record_node.args[1]
        for n in graph.nodes:
            if (
                n.op == "call_function"
                and "val" in n.meta
                and n.target
                not in (
                    torch.ops.streams.record_event.default,
                    torch.ops.streams.synchronize_event.default,
                )
            ):
                set_stream(n, stream_idx)

        wrap_all_sync_nodes_with_control_deps(gm)

        ctrl_nodes = list(graph.find_nodes(op="call_function", target=control_deps))
        # record_event + synchronize_event = 2 control_deps nodes
        self.assertEqual(len(ctrl_nodes), 2)
        record_ctrl = ctrl_nodes[0]
        sync_ctrl = ctrl_nodes[1]

        # synchronize_event's control_deps should depend on record's ctrl
        self.assertIn(record_ctrl, sync_ctrl.args[0])

        # The record should thread through the add (y = x + 1)
        record_getitems = [
            n
            for n in graph.nodes
            if n.op == "call_function"
            and n.target == operator.getitem
            and n.args[0] is record_ctrl
        ]
        self.assertGreaterEqual(len(record_getitems), 1)

        # Those getitems should be passed through synchronize's control_deps
        # as additional args (the passthrough deps)
        sync_passthrough_args = sync_ctrl.args[2:]  # skip (deps_tuple, subgraph)
        for getitem in record_getitems:
            self.assertIn(
                getitem,
                sync_passthrough_args,
                "record_event's getitem should be threaded through synchronize_event",
            )

        # The mul (z = y * 2) should consume a getitem from synchronize's
        # control_deps, not directly from record's.
        sync_getitems = [
            n
            for n in graph.nodes
            if n.op == "call_function"
            and n.target == operator.getitem
            and n.args[0] is sync_ctrl
        ]
        self.assertGreaterEqual(len(sync_getitems), 1)

        # Find the mul node and verify it uses a sync getitem
        mul_nodes = [
            n
            for n in graph.nodes
            if n.op == "call_function" and n.target == torch.ops.aten.mul.Tensor
        ]
        self.assertEqual(len(mul_nodes), 1)
        mul_args = set(mul_nodes[0].args)
        self.assertTrue(
            mul_args & set(sync_getitems),
            "mul should depend on synchronize_event's getitem, not record_event's",
        )