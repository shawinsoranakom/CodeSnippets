def test_alexnet1(self):
        alexnet = models.alexnet()
        symbolic_traced: torch.fx.GraphModule = symbolic_trace(alexnet)

        for n in symbolic_traced.graph.nodes:
            n.type = Dyn

        # print(symbolic_traced)

        res = alexnet.forward(torch.rand(10, 3, 227, 227)).size()
        constraints = transform_all_constraints(symbolic_traced, counter=0)
        solver = z3.Solver()
        solver.add(constraints)
        self.assertEqual(solver.check(), z3.sat)
        input = z3.Const(1, tensor_type)
        conv = z3.Const(2, tensor_type)
        solver.add(
            input == tensor_type.tensor4(D(1, 10), D(1, 3), D(1, 227), D(1, 227))
        )
        self.assertEqual(solver.check(), z3.sat)
        expected_conv = tensor_type.tensor4(D(1, 10), D(1, 64), D(1, 56), D(1, 56))
        if solver.model()[conv] != expected_conv:
            raise AssertionError(
                f"Expected conv == {expected_conv}, got {solver.model()[conv]}"
            )

        relu = z3.Const(7, tensor_type)
        expected_relu = tensor_type.tensor4(D(1, 10), D(1, 64), D(1, 56), D(1, 56))
        if solver.model()[relu] != expected_relu:
            raise AssertionError(
                f"Expected relu == {expected_relu}, got {solver.model()[relu]}"
            )

        maxpool = z3.Const(8, tensor_type)
        expected_maxpool = tensor_type.tensor4(D(1, 10), D(1, 64), D(1, 27), D(1, 27))
        if solver.model()[maxpool] != expected_maxpool:
            raise AssertionError(
                f"Expected maxpool == {expected_maxpool}, got {solver.model()[maxpool]}"
            )

        maxpool2 = z3.Const(42, tensor_type)
        expected_maxpool2 = tensor_type.tensor4(D(1, 10), D(1, 256), D(1, 6), D(1, 6))
        if solver.model()[maxpool2] != expected_maxpool2:
            raise AssertionError(
                f"Expected maxpool2 == {expected_maxpool2}, "
                f"got {solver.model()[maxpool2]}"
            )

        flatten = z3.Const(52, tensor_type)
        expected_flatten = tensor_type.tensor2(D(1, 10), D(1, 9216))
        if solver.model()[flatten] != expected_flatten:
            raise AssertionError(
                f"Expected flatten == {expected_flatten}, got {solver.model()[flatten]}"
            )

        linear = z3.Const(64, tensor_type)
        expected_linear = tensor_type.tensor2(D(1, 10), D(1, 4096))
        if solver.model()[linear] != expected_linear:
            raise AssertionError(
                f"Expected linear == {expected_linear}, got {solver.model()[linear]}"
            )

        linear2 = z3.Const(109, tensor_type)
        expected_linear2 = tensor_type.tensor2(D(1, res[0]), D(1, res[1]))
        if solver.model()[linear2] != expected_linear2:
            raise AssertionError(
                f"Expected linear2 == {expected_linear2}, got {solver.model()[linear2]}"
            )