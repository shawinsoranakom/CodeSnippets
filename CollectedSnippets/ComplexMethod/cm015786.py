def test_local_function_predefined_attributes(self):
        class M(torch.nn.Module):
            num_layers: int

            def __init__(self, num_layers):
                super().__init__()
                self.num_layers = num_layers
                self.lns = torch.nn.ModuleList(
                    [torch.nn.LayerNorm(3, eps=1e-4) for _ in range(num_layers)]
                )

            def forward(self, x):
                for ln in self.lns:
                    x = ln(x)
                return x

        x = torch.randn(2, 3)
        f = io.BytesIO()
        model = M(3)
        torch.onnx.export(
            model,
            (x,),
            f,
            export_modules_as_functions=True,
            opset_version=self.opset_version,
            dynamo=False,
        )

        onnx_model = onnx.load(io.BytesIO(f.getvalue()))
        funcs = onnx_model.functions
        m_funcs = [fn for fn in funcs if fn.name == "M"]
        self.assertEqual(m_funcs[0].attribute, ["num_layers"])
        ln_funcs = [fn for fn in funcs if fn.name == "LayerNorm"]
        self.assertEqual(ln_funcs[0].attribute, ["eps", "elementwise_affine"])

        from onnx import helper

        m_node = [n for n in onnx_model.graph.node if n.op_type == "M"]
        self.assertEqual(
            m_node[0].attribute[0],
            helper.make_attribute("num_layers", model.num_layers),
        )

        ln_nodes = [n for n in m_funcs[0].node if n.op_type == "LayerNorm"]
        expected_ln_attrs = [
            helper.make_attribute(
                "elementwise_affine", model.lns[0].elementwise_affine
            ),
            helper.make_attribute("eps", model.lns[0].eps),
        ]
        for ln_node in ln_nodes:
            self.assertIn(ln_node.attribute[0], expected_ln_attrs)
            self.assertIn(ln_node.attribute[1], expected_ln_attrs)