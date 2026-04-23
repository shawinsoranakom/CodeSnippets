def _is_packable_convolution(match):
        """
        Check if the node is supported for MKLDNN convolution.
        """
        conv_node = match.output_node()
        device_type = conv_node.meta.get("val").device.type
        # The operator 'mkldnn::_convolution_transpose_pointwise' is not currently implemented for the XPU device.
        if match.kwargs["is_transposed"] and device_type == "xpu":
            return False

        input_meta_value = conv_node.args[0].meta.get("val")
        weight_meta_value = conv_node.args[1].meta.get("val")
        if input_meta_value is None or weight_meta_value is None:
            return False
        input_size = input_meta_value.shape
        if conv_node.args[1].op != "get_attr":
            return False
        for meta_value in [input_meta_value, weight_meta_value]:
            if (
                meta_value is None
                or meta_value.device.type not in SUPPORTED_MKLDNN_DEVICES
                or (meta_value.dim() != 4 and meta_value.dim() != 5)
            ):
                return False

        if (
            input_meta_value.dtype == torch.bfloat16
            or weight_meta_value.dtype == torch.bfloat16
        ):
            if not is_mkldnn_bf16_supported(device_type):
                return False
        if (
            input_meta_value.dtype == torch.float16
            or weight_meta_value.dtype == torch.float16
        ):
            if not is_mkldnn_fp16_supported(device_type):
                return False
        is_transposed = conv_node.args[-3]
        if is_transposed:
            # TODO: Support dynamic shape case for MKLDNN conv transpose.
            if has_free_symbols(input_size):
                return False
            groups = conv_node.args[-1]
            in_channels = weight_meta_value.size(0)
            # doesn't support group_depthwise_conv_transpose.
            if groups > 1 and groups == in_channels:
                return False
            # Port from: aten/src/ATen/native/Convolution.cpp:is_output_padding_big
            output_paddings = conv_node.args[-2]
            strides = conv_node.args[3]
            if any(
                output_padding >= stride
                for output_padding, stride in zip(output_paddings, strides)
            ):
                return False
        return True