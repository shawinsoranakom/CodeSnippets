def test_normalize_args_preserve_meta(self):
        class MyModule(torch.nn.Module):
            def forward(self, a):
                return torch.add(a, 3)

        m = MyModule()
        traced = symbolic_trace(m)

        for node in traced.graph.nodes:
            if node.op == "call_function" and node.target == torch.add:
                node.meta["my_key"] = 7
                break
        else:
            self.fail("Didn't find call_function torch.add")

        input = torch.randn(2, 3)
        ShapeProp(traced).propagate(input)
        traced = NormalizeArgs(traced).transform()

        for node in traced.graph.nodes:
            if node.op == "call_function" and node.target == torch.add:
                self.assertTrue("my_key" in node.meta)
                self.assertEqual(node.meta["my_key"], 7)
                break
        else:
            self.fail("Didn't find call_function torch.add")