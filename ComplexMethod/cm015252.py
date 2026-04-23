def test_duplicated_getitem(self):
        class Foo(torch.nn.Module):
            def forward(self, x):
                return torch.topk(x, 2)

        foo = Foo()
        inputs = (torch.randn(3),)
        ep = torch.export.export(foo, inputs, strict=False)

        graph_module = copy.deepcopy(ep.graph_module)

        call_function_node = None
        num_getitems = 0
        for node in graph_module.graph.nodes:
            if (
                node.op == "call_function"
                and node.target == torch.ops.aten.topk.default
            ):
                call_function_node = node
            elif node.op == "call_function" and node.target == operator.getitem:
                self.assertIs(node.args[0], call_function_node)
                num_getitems += 1

        self.assertIsNotNone(call_function_node)
        self.assertEqual(num_getitems, 2)

        output_node = list(graph_module.graph.nodes)[-1]

        nodes = []
        with graph_module.graph.inserting_before(output_node):
            nodes.append(
                graph_module.graph.call_function(
                    operator.getitem, (call_function_node, 1)
                )
            )
            nodes.append(
                graph_module.graph.call_function(
                    operator.getitem, (call_function_node, 0)
                )
            )
            nodes.append(
                graph_module.graph.call_function(
                    operator.getitem, (call_function_node, 0)
                )
            )
            nodes.append(
                graph_module.graph.call_function(
                    operator.getitem, (call_function_node, 1)
                )
            )
        signature = ExportGraphSignature(
            input_specs=ep.graph_signature.input_specs,
            output_specs=ep.graph_signature.output_specs
            + [
                OutputSpec(
                    kind=OutputKind.USER_OUTPUT,
                    arg=TensorArgument(name=node.name),
                    target=None,
                )
                for node in nodes
            ],
        )
        output_node.args = (output_node.args[0] + tuple(nodes),)
        graph_module.recompile()
        new_ep = ep._update(graph_module, signature)

        new_num_getitems = 0
        for node in new_ep.graph.nodes:
            if (
                node.op == "call_function"
                and node.target == torch.ops.aten.topk.default
            ):
                call_function_node = node
            elif node.op == "call_function" and node.target == operator.getitem:
                self.assertIs(node.args[0], call_function_node)
                new_num_getitems += 1
        self.assertEqual(num_getitems, new_num_getitems)
        self.assertEqual(
            len(list(new_ep.graph.nodes)[-1].args[0]), len(signature.output_specs)
        )