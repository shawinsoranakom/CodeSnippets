def test_setType_maintains_output_shape_for_single_custom_op_with_onnx_ops(self):
        self.addCleanup(torch.onnx.unregister_custom_op_symbolic, "::linalg_inv", 9)

        class CustomInverse(torch.nn.Module):
            def forward(self, x, y, z):
                x = torch.inverse(x)
                return x + y + z

        def linalg_inv_settype(g, self):
            return g.op("com.microsoft::Inverse", self).setType(
                self.type().with_dtype(torch.float).with_sizes([2, 3, 10, 10])
            )

        torch.onnx.register_custom_op_symbolic("::linalg_inv", linalg_inv_settype, 9)
        model = CustomInverse()
        x = torch.randn(2, 3, 10, 10)
        y = torch.randn(2, 3, 10, 10)
        z = torch.randn(2, 3, 10, 10)
        f = io.BytesIO()
        torch.onnx.export(
            model,
            (x, y, z),
            f,
            opset_version=self.opset_version,
            custom_opsets={"com.microsoft": 1},
            dynamo=False,
        )

        model_proto = onnx.load(io.BytesIO(f.getvalue()))
        # To validate the shape of inverse Op, we need to find inverse output name,
        # and then use it to identify its value_info for the shape.
        output_name = ""
        for node in model_proto.graph.node:
            if node.op_type == "Inverse":
                output_name = node.output[0]
                break
        if not output_name:
            raise AssertionError("output_name not found")
        model_value_info = model_proto.graph.value_info
        self.assertIsNotNone(model_value_info)
        if not model_value_info:
            raise AssertionError("model_value_info is empty")
        for value_info in model_value_info:
            if not value_info.name:
                raise AssertionError("value_info.name is empty")
            if value_info.name == output_name:
                dims = value_info.type.tensor_type.shape.dim
                for i in range(len(dims)):
                    # If node output has shape info, it should have dim_value
                    # Otherwise, it has dim_params with dynamic shape
                    self.assertTrue(dims[i].HasField("dim_value"))
                for dim, rank in zip(dims, x.size()):
                    self.assertEqual(dim.dim_value, rank)