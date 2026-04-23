def test_conv_reshape_add_0_2(self):
        class BasicBlock(torch.nn.Module):
            def __init__(
                self,
                in_planes,
                out_planes,
                kernel_size,
                stride,
                padding,
                groups,
                dilation,
            ):
                super().__init__()
                self.conv1 = torch.nn.Conv2d(
                    in_channels=in_planes,
                    out_channels=out_planes,
                    kernel_size=kernel_size,
                    stride=stride,
                    padding=padding,
                    groups=groups,
                    bias=False,
                    dilation=dilation,
                )

            def forward(self, x: Dyn, y: TensorType([4, 1])):
                return torch.add(self.conv1(torch.reshape(x, (1, 2, 10, 20))), y)

        B = BasicBlock(2, 2, 2, 3, 2, 2, 2)

        #        4,1
        # 1, 2, 4, 8
        res = B.forward(torch.rand(20, 20), torch.rand(1, 2, 4, 8)).size()
        ast_rewriter = RewritingTracer()
        graph = ast_rewriter.trace(B)
        traced = GraphModule(ast_rewriter.root, graph, "gm")
        new_transformed_c = transform_all_constraints(traced)
        solver = z3.Solver()
        solver.add(new_transformed_c)
        self.assertEqual(solver.check(), z3.sat)

        conv_result = z3.Const(4, tensor_type)
        add_result = z3.Const(9, tensor_type)
        input_2 = z3.Const(2, tensor_type)

        s1, s2, s3, s4 = z3.Ints("x1 x2 x3 x4")
        s11, s22, s33, s44 = z3.Ints("x11 x22 x33 x44")
        d1, d2, d3, d4 = (
            D(s11, s1),
            D(s22, s2),
            D(s33, s3),
            D(s44, s4),
        )

        solver.add(conv_result == tensor_type.tensor4(d1, d2, d3, d4))
        solver.check()
        if solver.model()[s1].as_long() != res[0]:
            raise AssertionError(
                f"Expected s1 == {res[0]}, got {solver.model()[s1].as_long()}"
            )
        if solver.model()[s2].as_long() != res[1]:
            raise AssertionError(
                f"Expected s2 == {res[1]}, got {solver.model()[s2].as_long()}"
            )
        if solver.model()[s3].as_long() != res[2]:
            raise AssertionError(
                f"Expected s3 == {res[2]}, got {solver.model()[s3].as_long()}"
            )
        if solver.model()[s4].as_long() != res[3]:
            raise AssertionError(
                f"Expected s4 == {res[3]}, got {solver.model()[s4].as_long()}"
            )

        solver.add(input_2 == tensor_type.tensor2(D(1, 4), D(1, 1)))
        self.assertEqual(solver.check(), z3.sat)
        solver.add(add_result == tensor_type.tensor4(d1, d2, d3, d4))
        self.assertEqual(solver.check(), z3.sat)

        # first dimension could be anything because we have broadcasting
        if solver.model()[s1] != res[0]:
            raise AssertionError(f"Expected s1 == {res[0]}, got {solver.model()[s1]}")
        if solver.model()[s2] != res[1]:
            raise AssertionError(f"Expected s2 == {res[1]}, got {solver.model()[s2]}")
        if solver.model()[s3] != res[2]:
            raise AssertionError(f"Expected s3 == {res[2]}, got {solver.model()[s3]}")
        if solver.model()[s4] != res[3]:
            raise AssertionError(f"Expected s4 == {res[3]}, got {solver.model()[s4]}")