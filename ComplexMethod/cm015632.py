def test_external_event_synchronize_threads_inputs(self) -> None:
        """When the event was recorded externally, synchronize threads graph inputs through."""

        def fn(x):
            e = torch.Event()
            y = x + 1
            e.record()
            e.synchronize()
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

        from torch._functorch._aot_autograd.streams import (
            set_stream,
            wrap_all_sync_nodes_with_control_deps,
        )

        # Remove the record_event to simulate an externally-recorded event.
        record_node = next(
            n
            for n in graph.nodes
            if n.op == "call_function"
            and n.target is torch.ops.streams.record_event.default
        )
        stream_idx = record_node.args[1]
        graph.erase_node(record_node)

        # Set stream metadata on compute nodes.
        for n in graph.nodes:
            if (
                n.op == "call_function"
                and "val" in n.meta
                and n.target is not torch.ops.streams.synchronize_event.default
            ):
                set_stream(n, stream_idx)

        wrap_all_sync_nodes_with_control_deps(gm)
        gm.recompile()

        self.assertExpectedInline(
            print_graph(gm),
            """\
class <lambda>(torch.nn.Module):
    def forward(self, arg0_1: "f32[2, 2]"):
        # Annotation: {'stream': 0}
        add: "f32[2, 2]" = torch.ops.aten.add.Tensor(arg0_1, 1)

        # No stacktrace found for following nodes
        subgraph_synchronize_event = self.subgraph_synchronize_event
        control_deps = torch.ops.higher_order.control_deps((arg0_1, add), subgraph_synchronize_event, add);  arg0_1 = add = subgraph_synchronize_event = None

        # Annotation: {'stream': 0}
        getitem: "f32[2, 2]" = control_deps[1];  control_deps = None

        # Annotation: {'stream': 0}
        mul: "f32[2, 2]" = torch.ops.aten.mul.Tensor(getitem, 2);  getitem = None
        return (mul,)

    class subgraph_synchronize_event(torch.nn.Module):
        def forward(self, dep_0: "f32[2, 2]"):
            #
            synchronize_event_default = torch.ops.streams.synchronize_event.default(1)
            return (synchronize_event_default, dep_0)
""",
        )