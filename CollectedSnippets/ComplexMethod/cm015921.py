def test_type_check_conv2D_2_fully_static(self):
        annotation_list = [
            (1, 2, 3, 5),
            (2, 5, 6, 9),
            (10, 15, 13, 14),
            (10, Dyn, 13, 14),
            (Dyn, Dyn, Dyn, 3),
        ]
        input_list = [
            (1, 2, 3, 5),
            (2, 5, 6, 9),
            (10, 15, 13, 14),
            (10, 15, 13, 14),
            (1, 2, 2, 3),
        ]
        intermediate_types = [
            (1, Dyn, Dyn, 7),
            (2, Dyn, 4, 6),
            (10, 15, Dyn, 5),
            (10, 15, 7, 7),
            (1, Dyn, Dyn, Dyn),
        ]
        in_planes_list = [2, 5, 15, 15, 2]
        stride_list = [1, 2, 3, 2, 2]
        out_planes_list = [2, 5, 15, 15, 2]
        groups_list = [1, 5, 5, 5, 2]
        dilation_list = [1, 2, 3, 3, 3]
        padding_list = [1, 2, 3, 3, 3]
        kernel_size_list = [1, 2, 3, 3, 3]
        output_types = [
            (1, 2, Dyn, 7),
            (2, 5, 4, 6),
            (10, 15, Dyn, 5),
            (10, 15, 7, 7),
            (1, 2, Dyn, Dyn),
        ]

        for i in range(5):
            annotation = annotation_list[i]
            input = input_list[i]
            in_planes = in_planes_list[i]
            stride = stride_list[i]
            out_planes = out_planes_list[i]
            groups = groups_list[i]
            dilation = dilation_list[i]
            padding = padding_list[i]
            kernel_size = kernel_size_list[i]
            intermediate_type = intermediate_types[i]

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

                def forward(self, x):
                    out = self.conv1(x)
                    return out

            B = BasicBlock(
                in_planes, out_planes, kernel_size, stride, padding, groups, dilation
            )
            ast_rewriter = RewritingTracer()
            graph = ast_rewriter.trace(B)
            traced = GraphModule(ast_rewriter.root, graph, "gm")

            # annotate our argument
            for n in graph.nodes:
                if n.op == "placeholder":
                    n.type = TensorType(annotation)

            b = B.forward(torch.rand(input))
            tc = GraphTypeChecker({}, traced)
            tc.type_check()

            for n in graph.nodes:
                if n.op == "output":
                    if not is_consistent(n.type, TensorType(b.size())):
                        raise AssertionError(
                            f"Expected n.type consistent with TensorType({b.size()})"
                        )

            # test with intermediate annotations
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

                def forward(self, x):
                    out = self.conv1(x)
                    return out

            B = BasicBlock(
                in_planes, out_planes, kernel_size, stride, padding, groups, dilation
            )
            ast_rewriter = RewritingTracer()
            graph = ast_rewriter.trace(B)
            traced = GraphModule(ast_rewriter.root, graph, "gm")

            # populate our intermediate notes
            for n in traced.graph.nodes:
                if n.op == "call_module":
                    n.type = TensorType(intermediate_type)

            tc = GraphTypeChecker({}, traced)
            tc.type_check()

            for n in traced.graph.nodes:
                if n.op == "output":
                    if n.type != TensorType(output_types[i]):
                        raise AssertionError(
                            f"Expected n.type == TensorType({output_types[i]}), "
                            f"got {n.type}"
                        )
                    if not is_consistent(n.type, TensorType(b.size())):
                        raise AssertionError(
                            f"Expected n.type consistent with TensorType({b.size()})"
                        )