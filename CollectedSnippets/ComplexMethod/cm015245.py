def test_preserve_shape_dynamism_for_unused_inputs(self):
        torch.export.register_dataclass(
            Inp3,
            serialized_type_name="test_preserve_shape_dynamism_for_unused_inputs.Inp3",
        )

        class Module(torch.nn.Module):
            def forward(self, x: Inp3):
                return x.f + 1

        mod = Module()
        example_inputs = (Inp3(f=torch.ones(10, 4), p=torch.zeros(10, 4)),)
        ep_static = export(mod, example_inputs)
        for node in ep_static.graph.nodes:
            if node.op == "placeholder":
                for s in node.meta["val"].shape:
                    self.assertIsInstance(s, int)

        dim0_x_f, dim0_x_p = torch.export.dims("dim0_x_f", "dim0_x_p")
        dynamic_shapes = {"x": [{0: dim0_x_f}, {0: dim0_x_p}]}
        ep_dynamic = export(mod, example_inputs, dynamic_shapes=dynamic_shapes)
        for node in ep_dynamic.graph.nodes:
            if node.op == "placeholder":
                for i, s in enumerate(node.meta["val"].shape):
                    if i == 0:
                        self.assertIsInstance(s, torch.SymInt)
                    else:
                        self.assertIsInstance(s, int)