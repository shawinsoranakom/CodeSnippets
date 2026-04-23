def test_type_check_conv2D(self):
        class BasicBlock(torch.nn.Module):
            def __init__(self, inplanes, planes, stride=1):
                super().__init__()
                norm_layer = torch.nn.BatchNorm2d
                self.conv1 = conv3x3(inplanes, planes, stride)
                self.bn1 = norm_layer(planes)

            def forward(self, x: Dyn):
                identity = x
                out: TensorType((2, 2, Dyn, 4)) = self.conv1(x)
                out += identity
                return out

        B = BasicBlock(2, 2)
        ast_rewriter = RewritingTracer()
        graph = ast_rewriter.trace(B)
        traced = GraphModule(ast_rewriter.root, graph, "gm")
        tc = GraphTypeChecker({}, traced)
        tc.type_check()
        for n in graph.nodes:
            if n.op == "placeholder":
                if n.type != TensorType((Dyn, Dyn, Dyn, Dyn)):
                    raise AssertionError(
                        f"Expected n.type == TensorType((Dyn, Dyn, Dyn, Dyn)), "
                        f"got {n.type}"
                    )
            if n.op == "call_function":
                if n.type != TensorType((Dyn, Dyn, Dyn, Dyn)):
                    raise AssertionError(
                        f"Expected n.type == TensorType((Dyn, Dyn, Dyn, Dyn)), "
                        f"got {n.type}"
                    )
            if n.op == "output":
                if n.type != TensorType((Dyn, Dyn, Dyn, Dyn)):
                    raise AssertionError(
                        f"Expected n.type == TensorType((Dyn, Dyn, Dyn, Dyn)), "
                        f"got {n.type}"
                    )
            if n.op == "call_module":
                if n.type != TensorType((2, 2, Dyn, 4)):
                    raise AssertionError(
                        f"Expected n.type == TensorType((2, 2, Dyn, 4)), got {n.type}"
                    )