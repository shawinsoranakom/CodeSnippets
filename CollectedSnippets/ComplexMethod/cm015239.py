def test_custom_class(self):
        custom_obj = torch.classes._TorchScriptTesting._PickleTester([3, 4])

        class Foo(torch.nn.Module):
            def forward(self, x):
                return x + x

        f = Foo()

        inputs = (torch.zeros(4, 4),)
        ep = export(f, inputs, strict=True)

        # Replace one of the values with an instance of our custom class
        for node in ep.graph.nodes:
            if node.op == "call_function" and node.target == torch.ops.aten.add.Tensor:
                with ep.graph.inserting_before(node):
                    custom_node = ep.graph.call_function(
                        torch.ops._TorchScriptTesting.take_an_instance.default,
                        (custom_obj,),
                    )
                    custom_node.meta["val"] = torch.ones(4, 4)
                    custom_node.meta["torch_fn"] = (
                        "take_an_instance",
                        "take_an_instance",
                    )
                    arg0, _ = node.args
                    node.args = (arg0, custom_node)

        serialized_vals = serialize(ep)

        ep_str = serialized_vals.exported_program.decode("utf-8")
        if "class_fqn" not in ep_str:
            raise AssertionError("'class_fqn' not found in serialized output")
        if custom_obj._type().qualified_name() not in ep_str:
            raise AssertionError(
                f"'{custom_obj._type().qualified_name()}' not found in serialized output"
            )

        deserialized_ep = deserialize(serialized_vals)

        for node in deserialized_ep.graph.nodes:
            if (
                node.op == "call_function"
                and node.target
                == torch.ops._TorchScriptTesting.take_an_instance.default
            ):
                arg = node.args[0]
                self.assertTrue(isinstance(arg, torch._C.ScriptObject))
                self.assertEqual(arg._type(), custom_obj._type())
                self.assertEqual(arg.__getstate__(), custom_obj.__getstate__())
                self.assertEqual(arg.top(), 7)