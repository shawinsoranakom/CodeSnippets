def test_type_check_reshape_true(self):
        class M(torch.nn.Module):
            def forward(self, x: TensorType((1, 6))):
                return torch.reshape(x, [1, 2, 3])

        module = M()
        symbolic_traced: torch.fx.GraphModule = symbolic_trace(module)
        tc = GraphTypeChecker({}, symbolic_traced)
        self.assertTrue(tc.type_check())

        for n in symbolic_traced.graph.nodes:
            if n.op == "placeholder":
                if n.type != TensorType((1, 6)):
                    raise AssertionError(
                        f"Expected n.type == TensorType((1, 6)), got {n.type}"
                    )

            if n.op == "call_function":
                if n.type != TensorType((1, 2, 3)):
                    raise AssertionError(
                        f"Expected n.type == TensorType((1, 2, 3)), got {n.type}"
                    )

            if n.op == "output":
                if n.type != TensorType((1, 2, 3)):
                    raise AssertionError(
                        f"Expected n.type == TensorType((1, 2, 3)), got {n.type}"
                    )