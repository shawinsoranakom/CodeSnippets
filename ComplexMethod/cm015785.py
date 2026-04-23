def test_local_function(self):
        class N(torch.nn.Module):
            def __init__(self, prob):
                super().__init__()
                self.dropout = torch.nn.Dropout(prob)

            def forward(self, x):
                return self.dropout(x)

        class M(torch.nn.Module):
            def __init__(self, num_layers):
                super().__init__()
                self.num_layers = num_layers
                self.lns = torch.nn.ModuleList(
                    [torch.nn.LayerNorm(3, eps=i) for i in range(num_layers)]
                )
                self.celu1 = torch.nn.CELU(1.0)
                self.celu2 = torch.nn.CELU(2.0)
                self.dropout = N(0.5)

            def forward(self, x, y, z):
                res1 = self.celu1(x)
                res2 = self.celu2(y)
                for ln in self.lns:
                    z = ln(z)
                return res1 + res2, self.dropout(z)

        x = torch.randn(2, 3)
        y = torch.randn(2, 3)
        z = torch.randn(2, 3)

        # Export specified modules. Test against specifying modules that won't
        # exist in the exported model.
        # Model export in inference mode will remove dropout node,
        # thus the dropout module no longer exist in graph.
        f = io.BytesIO()
        torch.onnx.export(
            M(3),
            (x, y, z),
            f,
            opset_version=self.opset_version,
            export_modules_as_functions={
                torch.nn.CELU,
                torch.nn.Dropout,
                torch.nn.LayerNorm,
            },
            dynamo=False,
        )

        onnx_model = onnx.load(io.BytesIO(f.getvalue()))

        # Check function definition
        funcs = onnx_model.functions
        celu_funcs = [f for f in funcs if f.name == "CELU"]
        self.assertEqual(len(celu_funcs), 1)
        self.assertEqual(celu_funcs[0].domain, "torch.nn.modules.activation")
        self.assertEqual(len(celu_funcs[0].attribute), 3)
        ln_funcs = [f for f in funcs if f.name == "LayerNorm"]
        self.assertEqual(len(ln_funcs), 1)
        self.assertEqual(ln_funcs[0].domain, "torch.nn.modules.normalization")
        self.assertEqual(len(ln_funcs[0].attribute), 3)

        # Check local function nodes
        nodes = onnx_model.graph.node
        celu_ns = [n for n in nodes if n.op_type == "CELU"]
        ln_ns = [n for n in nodes if n.op_type == "LayerNorm"]
        self.assertEqual(len(celu_ns), 2)
        self.assertEqual(celu_ns[0].domain, "torch.nn.modules.activation")
        self.assertEqual(len(celu_ns[0].attribute), 3)
        self.assertEqual(len(ln_ns), 3)
        self.assertEqual(ln_ns[0].domain, "torch.nn.modules.normalization")
        self.assertEqual(len(ln_ns[0].attribute), 3)

        # Export specified modules.
        f = io.BytesIO()
        torch.onnx.export(
            M(3),
            (x, y, z),
            f,
            opset_version=self.opset_version,
            export_modules_as_functions={torch.nn.CELU},
            dynamo=False,
        )

        onnx_model = onnx.load(io.BytesIO(f.getvalue()))
        funcs = onnx_model.functions
        self.assertEqual(len(funcs), 1)
        self.assertEqual(funcs[0].name, "CELU")

        # Export with empty specified modules. Normal export.
        f = io.BytesIO()
        torch.onnx.export(
            M(3),
            (x, y, z),
            f,
            opset_version=self.opset_version,
            export_modules_as_functions=set(),
            dynamo=False,
        )

        onnx_model = onnx.load(io.BytesIO(f.getvalue()))
        funcs = onnx_model.functions
        self.assertEqual(len(funcs), 0)

        # Export all modules. Should contain {M, CELU, LayerNorm}.
        f = io.BytesIO()
        torch.onnx.export(
            M(3),
            (x, y, z),
            f,
            opset_version=self.opset_version,
            export_modules_as_functions=True,
            dynamo=False,
        )

        onnx_model = onnx.load(io.BytesIO(f.getvalue()))
        funcs = onnx_model.functions
        self.assertEqual(len(funcs), 3)