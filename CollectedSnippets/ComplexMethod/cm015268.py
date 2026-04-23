def _validate_setattr_fp_weights(self, model, num_nodes):
        quantize_forward_graph = model.quantize_forward.graph
        fp_weights_setattr = 0
        fp_weight_names = []
        for n in quantize_forward_graph.nodes():
            if n.kind() == "prim::SetAttr":
                maybe_packed_param = n.inputsAt(1).node()
                if maybe_packed_param.kind() == "quantized::linear_prepack":
                    weight_name = OnDevicePTQUtils.get_linear_packed_param_fp_weight(
                        maybe_packed_param
                    )
                    fp_weight_names.append(weight_name)

        for n in quantize_forward_graph.nodes():
            # This is basically detecting
            # %x = prim::Constant
            # = prim::SetAttr(<weight_name>)(module_value, x)
            # Thus making sure that the original fp weights are
            # reset
            if n.kind() == "prim::SetAttr":
                weight_name = n.s("name")
                if weight_name in fp_weight_names:
                    maybe_constant = n.inputsAt(1).node()
                    if maybe_constant.kind() == "prim::Constant":
                        fp_weights_setattr += 1
        self.assertEqual(fp_weights_setattr, num_nodes)