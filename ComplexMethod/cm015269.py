def _validate_quantized_forward(self, model, num_nodes):
        quantized_forward_graph = model.quantized_forward.graph
        quantize_per_tensor = quantize_per_channel = 0
        quantized_linear_dynamic = 0
        linear_packed_params = 0
        num_setattr = 0
        for n in quantized_forward_graph.nodes():
            if "aten::quantize_per_tensor" in n.kind():
                quantize_per_tensor += 1
            if "aten::quantize_per_channel" in n.kind():
                quantize_per_channel += 1
            if "quantized::linear_dynamic" in n.kind():
                quantized_linear_dynamic += 1
            if n.kind() == "prim::GetAttr":
                output = n.outputsAt(0)
                output_type = output.type()
                if "LinearPackedParamsBase" in output_type.str():
                    linear_packed_params += 1
            if n.kind() == "prim::SetAttr":
                num_setattr += 1
        self.assertEqual(quantize_per_tensor, 0)
        self.assertEqual(quantize_per_channel, 0)
        self.assertEqual(quantized_linear_dynamic, num_nodes)
        self.assertEqual(linear_packed_params, num_nodes)