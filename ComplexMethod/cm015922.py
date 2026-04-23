def test_type_maxpool2d_fully_static(self):
        annotation_list = [
            (Dyn, Dyn, 3, 5),
            (2, 5, 6, 9),
            (10, 15, 13, 14),
            (10, Dyn, 13, 14),
            (Dyn, Dyn, Dyn, 10),
        ]
        input_list = [
            (1, 2, 3, 5),
            (2, 5, 6, 9),
            (10, 15, 13, 14),
            (10, 15, 13, 14),
            (2, 2, 10, 10),
        ]
        intermediate_types = [
            (1, 2, Dyn, Dyn),
            (2, Dyn, 2, 4),
            (10, 15, Dyn, 2),
            (10, 15, 2, 3),
            (2, Dyn, Dyn, Dyn),
        ]
        stride_list = [1, 2, 3, 2, 1]
        dilation_list = [1, 2, 3, 3, 2]
        padding_list = [1, 2, 3, 3, 1]
        kernel_size_list = [2, 4, 6, 6, 3]
        output_types = [
            (1, 2, 4, 6),
            (2, 5, 2, 4),
            (10, 15, 2, 2),
            (10, 15, 2, 3),
            (2, Dyn, Dyn, 8),
        ]

        for i in range(5):
            annotation = annotation_list[i]
            input = input_list[i]
            stride = stride_list[i]
            dilation = dilation_list[i]
            padding = padding_list[i]
            kernel_size = kernel_size_list[i]
            intermediate_type = intermediate_types[i]

            class BasicBlock(torch.nn.Module):
                def __init__(self, kernel_size, stride, padding, dilation):
                    super().__init__()
                    self.pool = torch.nn.MaxPool2d(
                        kernel_size,
                        stride=stride,
                        padding=padding,
                        dilation=dilation,
                        return_indices=False,
                        ceil_mode=False,
                    )

                def forward(self, x):
                    out = self.pool(x)
                    return out

            B = BasicBlock(kernel_size, stride, padding, dilation)
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
                def __init__(self, kernel_size, stride, padding, dilation):
                    super().__init__()
                    self.pool = torch.nn.MaxPool2d(
                        kernel_size,
                        stride=stride,
                        padding=padding,
                        dilation=dilation,
                        return_indices=False,
                        ceil_mode=False,
                    )

                def forward(self, x):
                    out = self.pool(x)
                    return out

            B = BasicBlock(kernel_size, stride, padding, dilation)
            ast_rewriter = RewritingTracer()
            graph = ast_rewriter.trace(B)
            traced = GraphModule(ast_rewriter.root, graph, "gm")

            # annotate our argument
            for n in graph.nodes:
                if n.op == "placeholder":
                    n.type = TensorType(annotation)

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