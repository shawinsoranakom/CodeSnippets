def _inner(match):
        # Here we do some further check to ensure:
        # 1. It's a conv2d node with dim of 4, since we only support lowering of conv2d now.
        # 2. The dequant pattern has only 1 user of conv2d node.
        # If these conditions don't meet, we will not
        # insert weight prepack node into the matched pattern.
        conv_node = match.output_node()
        assert conv_node.target is aten.convolution.default
        input_meta_value = conv_node.args[0].meta.get("val")
        weight_meta_value = conv_node.args[1].meta.get("val")
        for meta_value in [input_meta_value, weight_meta_value]:
            if (
                meta_value is None
                or (meta_value.device.type != "cpu" and meta_value.device.type != "xpu")
                or meta_value.dim() not in [3, 4]
            ):
                # Only support conv1d/2d now
                return False

        assert dtype in [torch.float32, torch.bfloat16]

        if not with_dtype_convert:
            dequant_node = conv_node.args[0]
        else:
            convert_to_bf16 = conv_node.args[0]
            dequant_node = convert_to_bf16.args[0]

        if len(list(dequant_node.users)) != 1:
            # Ensure the dequant pattern only has 1 user
            # since we will delete the dequant pattern here
            return False
        return True