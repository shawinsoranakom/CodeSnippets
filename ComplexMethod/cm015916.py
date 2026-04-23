def test_type_check_transpose_true(self):
        class M(torch.nn.Module):
            def forward(self, x: TensorType((1, 2, 3, 5))):
                return torch.transpose(x, 0, 1)

        module = M()
        symbolic_traced: torch.fx.GraphModule = symbolic_trace(module)
        tc = GraphTypeChecker({}, symbolic_traced)
        self.assertTrue(tc.type_check())

        for n in symbolic_traced.graph.nodes:
            if n.op == "call_function":
                if n.type != TensorType([2, 1, 3, 5]):
                    raise AssertionError(
                        f"Expected n.type == TensorType([2, 1, 3, 5]), got {n.type}"
                    )
            if n.op == "output":
                if n.type != TensorType([2, 1, 3, 5]):
                    raise AssertionError(
                        f"Expected n.type == TensorType([2, 1, 3, 5]), got {n.type}"
                    )
            if n.op == "x":
                if n.placeholder != TensorType([1, 2, 3, 5]):
                    raise AssertionError(
                        f"Expected n.placeholder == TensorType([1, 2, 3, 5]), "
                        f"got {n.placeholder}"
                    )