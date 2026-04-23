def test_conv_dyn(self):
        s1, s2, s3, s4 = z3.Ints("s1 s2 s3 s4")
        e1, e2, e3, e4 = z3.Ints("e1 e2 e3 e4")
        s11, s22, s33, s44 = z3.Ints("s11 s22 s33 s44")
        e11, e22, e33, e44 = z3.Ints("e11 e22 e33 e44")
        d1, d2, d3, d4 = (
            D(s11, s1),
            D(s22, s2),
            D(s33, s3),
            D(s44, s4),
        )
        b1, b2, b3, b4 = D(e11, e1), D(e22, e2), D(e33, e3), D(e44, e4)

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

            def forward(self, x: Dyn):
                return self.conv1(x)

        BasicBlock(2, 2, 2, 2, 2, 2, 2).forward(torch.rand(4, 2, 3, 4))

        ast_rewriter = RewritingTracer()
        graph = ast_rewriter.trace(BasicBlock(2, 2, 2, 2, 2, 2, 2))
        traced = GraphModule(ast_rewriter.root, graph, "gm")

        transformed = transform_all_constraints(traced)

        solver3 = z3.Solver()
        solver3.add(transformed)
        if solver3.check() != z3.sat:
            raise AssertionError(
                f"Expected solver3.check() == z3.sat, got {solver3.check()}"
            )

        x = z3.Const(1, tensor_type)
        y = z3.Const(2, tensor_type)

        solver3.add(
            x == tensor_type.tensor4(d1, d2, d3, d4),
            y == tensor_type.tensor4(b1, b2, b3, b4),
        )

        if solver3.check() != z3.sat:
            raise AssertionError(
                f"Expected solver3.check() == z3.sat, got {solver3.check()}"
            )
        if solver3.model()[s1].as_long() != solver3.model()[e1].as_long():
            raise AssertionError(
                f"Expected s1 == e1, got {solver3.model()[s1].as_long()} != "
                f"{solver3.model()[e1].as_long()}"
            )
        if solver3.model()[s11].as_long() != solver3.model()[e11].as_long():
            raise AssertionError(
                f"Expected s11 == e11, got {solver3.model()[s11].as_long()} != "
                f"{solver3.model()[e11].as_long()}"
            )

        solver3.add(s2 != 2)
        if solver3.check() != z3.sat:
            raise AssertionError(
                f"Expected solver3.check() == z3.sat, got {solver3.check()}"
            )
        if solver3.model()[s22].as_long() != 0:
            raise AssertionError(
                f"Expected s22 == 0, got {solver3.model()[s22].as_long()}"
            )

        solver3.add(s22 != 0)
        self.assertEqual(solver3.check(), z3.unsat)

        solver2 = z3.Solver()
        solver2.add(transformed)
        if solver2.check() != z3.sat:
            raise AssertionError(
                f"Expected solver2.check() == z3.sat, got {solver2.check()}"
            )
        solver2.add(x == tensor_type.tensor3(d1, d2, d3))
        self.assertEqual(solver2.check(), z3.unsat)