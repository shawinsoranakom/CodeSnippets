def test_split_const_gm_with_lifted_constants(self):
        class Model(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.w_pre = torch.randn(4, 4)
                self.b = torch.randn(4)

            def forward(self, x):
                w_transpose = torch.transpose(self.w_pre, 0, 1)
                w_relu = torch.nn.functional.relu(w_transpose)
                w = w_relu + self.b
                return (
                    torch.matmul(x, w) + self.b + torch.arange(4, dtype=torch.float16)
                )

        example_inputs = (torch.randn(4, 4),)
        mod = Model()
        ep = torch.export.export(mod, example_inputs)
        new_gm = copy.deepcopy(ep.graph_module)
        new_sig = copy.deepcopy(ep.graph_signature)
        placeholder_nodes = [
            node for node in new_gm.graph.nodes if node.op == "placeholder"
        ]
        constants = {**ep.state_dict, **ep.constants}
        lifted_constants = {
            n.name: constants[spec.target]
            for n, spec in zip(placeholder_nodes, new_sig.input_specs)
            if spec.target is not None
        }
        # [self.w_pre, self.b]
        lifted_constant_names = list(lifted_constants)
        lifted_constant_values = [lifted_constants[n] for n in lifted_constant_names]
        const_gm, _ = split_const_gm(new_gm, False, lifted_constant_names)
        counter = 0
        for node in const_gm.graph.nodes:
            if node.op == "call_function":
                counter += 1
        self.assertTrue(counter == 4)
        counter = 0
        for n in new_gm.graph.nodes:
            if n.op == "placeholder":
                counter += 1
        # expect 3 existing placeholders and 2 folded constant
        self.assertTrue(counter == 5)
        # return (self.b, folded_const, folded_const)
        const_folded_value = const_gm(*lifted_constant_values)

        test_input = torch.randn(4, 4)
        # new_gm(c_w_pre, b, x, folded_const, folded_const)
        actual = new_gm(
            lifted_constant_values[0],
            const_folded_value[0],
            test_input,
            const_folded_value[1],
            const_folded_value[2],
        )[0]
        expected = mod(test_input)
        self.assertEqual(actual, expected)
        const_gm, _ = split_const_gm(
            ep.graph_module, False, lifted_constant_names, lambda x: True
        )
        counter = 0
        for node in const_gm.graph.nodes:
            if node.op == "call_function":
                self.assertTrue(False)