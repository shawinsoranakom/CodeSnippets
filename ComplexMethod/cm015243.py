def test_from_node_metadata_export(self):
        class Foo(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv1d = torch.nn.Conv1d(3, 3, 3)
                self.conv2d = torch.nn.Conv2d(3, 3, 3)

            def forward(self, x):
                x = self.conv2d(x)
                x = x.squeeze(0)
                x = self.conv1d(x)
                return x

            def example_inputs(self):
                return

        f = Foo()
        inputs = (torch.randn(1, 3, 5, 5),)
        ep = export(f, inputs)
        graph_id = id(ep.graph)
        gm = ep.module()
        from torch.fx.traceback import NodeSourceAction

        for node in gm.graph.nodes:
            if node.op in ("placeholder", "output", "call_module"):
                continue
            if "weight" in node.name or "bias" in node.name:
                self.assertTrue(
                    node.meta["from_node"][-1].pass_name
                    == "ExportedProgram.module().unlift()"
                )
                self.assertTrue(
                    node.meta["from_node"][-1].action
                    == [NodeSourceAction.CREATE, NodeSourceAction.REPLACE]
                )
                self.assertEqual(
                    node.meta["from_node"][-1].from_node[-1].graph_id, graph_id
                )
            else:
                self.assertTrue(
                    node.meta["from_node"][-1].pass_name == "ExportedProgram.module()"
                )
                self.assertTrue(
                    node.meta["from_node"][-1].action == [NodeSourceAction.CREATE]
                )
                self.assertEqual(node.meta["from_node"][-1].graph_id, graph_id)

        ## re-export
        ep2 = export(gm, inputs)
        gm2 = ep2.module()
        graph_id = id(ep2.graph)

        for node in gm2.graph.nodes:
            if node.op in ("placeholder", "output", "call_module"):
                continue

            if "weight" in node.name or "bias" in node.name:
                self.assertTrue(
                    node.meta["from_node"][-1].pass_name
                    == "ExportedProgram.module().unlift()"
                )
                self.assertTrue(
                    node.meta["from_node"][-1].action
                    == [NodeSourceAction.CREATE, NodeSourceAction.REPLACE]
                )
                self.assertEqual(
                    node.meta["from_node"][-1].from_node[-1].graph_id, graph_id
                )
            else:
                self.assertTrue(
                    node.meta["from_node"][-1].pass_name == "ExportedProgram.module()"
                )
                self.assertTrue(
                    node.meta["from_node"][-1].action == [NodeSourceAction.CREATE]
                )
                self.assertEqual(node.meta["from_node"][-1].graph_id, graph_id)