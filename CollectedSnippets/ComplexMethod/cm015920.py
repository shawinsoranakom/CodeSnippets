def test_type_check_conv2D_2(self):
        class BasicBlock(torch.nn.Module):
            def __init__(self, inplanes, planes, stride=1):
                super().__init__()
                norm_layer = torch.nn.BatchNorm2d
                self.conv1 = conv3x3(inplanes, planes, stride)
                self.bn1 = norm_layer(planes)

            def forward(self, x: TensorType((5, 2, 3, 4))):
                identity = x
                out = self.conv1(x)
                out += identity
                return out

        B = BasicBlock(2, 2)
        b = B.forward(torch.rand(5, 2, 3, 4))

        ast_rewriter = RewritingTracer()
        graph = ast_rewriter.trace(B)
        traced = GraphModule(ast_rewriter.root, graph, "gm")
        tc = GraphTypeChecker({}, traced)
        tc.type_check()
        t = TensorType((5, 2, 3, 4))
        for n in graph.nodes:
            if n.op == "placeholder":
                if n.type != t:
                    raise AssertionError(f"Expected n.type == {t}, got {n.type}")
            if n.op == "call_function":
                if n.type != t:
                    raise AssertionError(f"Expected n.type == {t}, got {n.type}")
            if n.op == "output":
                if torch.Size(n.type.__args__) != b.shape:
                    raise AssertionError(
                        f"Expected torch.Size(n.type.__args__) == {b.shape}, "
                        f"got {torch.Size(n.type.__args__)}"
                    )
            if n.op == "call_module":
                if n.type != t:
                    raise AssertionError(f"Expected n.type == {t}, got {n.type}")

        B = BasicBlock(1, 2)
        ast_rewriter = RewritingTracer()
        graph = ast_rewriter.trace(B)
        traced = GraphModule(ast_rewriter.root, graph, "gm")
        tc = GraphTypeChecker({}, traced)
        with self.assertRaises(TypeError):
            tc.type_check()