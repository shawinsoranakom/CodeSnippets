def test_intermediate_shape_comp(self):
        class Foo(torch.nn.Module):
            def forward(self, x, y):
                z = torch.cat([x, x], dim=0)
                w = z.repeat(y.shape[0])
                return w.shape[0] + x.shape[0]

        inputs = (torch.randn(6), torch.randn(4))
        shapes = {
            "x": (Dim("dx0"),),
            "y": (Dim("dy"),),
        }
        ep = export(
            Foo(),
            inputs,
            dynamic_shapes=shapes,
        ).run_decompositions({})
        # test that shape is from size compute, not sym_size call
        add_node = [node for node in ep.graph.nodes if node.target == operator.add][0]
        self.assertTrue(add_node.args[0].target == operator.mul)
        # test sym_size calls only happen on placeholders
        sym_size_nodes = [
            node
            for node in ep.graph.nodes
            if node.target == torch.ops.aten.sym_size.int
        ]
        self.assertEqual(len(sym_size_nodes), 2)
        self.assertTrue(
            all(node.args[0].op == "placeholder" for node in sym_size_nodes)
        )
        # dynamo will DCE the repeat node, AOTAutograd will leave it
        # training IR will also DCE due to retracing
        repeat_nodes = [
            node
            for node in ep.graph.nodes
            if node.target == torch.ops.aten.repeat.default
        ]
        self.assertEqual(len(repeat_nodes), 0)