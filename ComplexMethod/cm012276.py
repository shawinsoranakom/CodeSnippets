def _is_packable_linear(match):
        """
        Check if the node is supported for MKLDNN linear.
        """

        def is_const_or_cat_by_const(weight):
            if weight.op == "get_attr":
                return True
            if weight.target != aten.cat.default:
                return False
            return all(arg.op == "get_attr" for arg in weight.args[0])

        linear_node = match.output_node()
        # mkldnn linear only supports beta=1or0 and alpha=1
        if linear_node.target is aten.addmm.default:
            alpha = linear_node.kwargs.get("alpha", 1.0)
            beta = linear_node.kwargs.get("beta", 1.0)
            if (beta != 0.0 and beta != 1.0) or alpha != 1.0:
                return False
        # weight_idx is 1 for aten.mm and is 2 for aten.addmm
        weight_idx = 2 if linear_node.target is aten.addmm.default else 1
        if not is_const_or_cat_by_const(linear_node.args[weight_idx]):
            return False
        input_meta_value = linear_node.args[weight_idx - 1].meta.get("val")
        weight_meta_value = linear_node.args[weight_idx].meta.get("val")
        if input_meta_value is None or weight_meta_value is None:
            return False
        if (
            input_meta_value.dtype == torch.float64
            or weight_meta_value.dtype == torch.float64
        ):
            return False
        is_lp_weight = weight_meta_value.dtype in (
            torch.bfloat16,
            torch.float16,
        )
        reduced_f32_matmul_enabled = torch.backends.mkldnn.matmul.fp32_precision in [  # type: ignore[attr-defined]
            "bf16",
            "tf32",
        ]
        use_reduced_f32_for_fp32_weight = (
            reduced_f32_matmul_enabled and weight_meta_value.dtype == torch.float32
        )
        compute_with_lp = is_lp_weight or use_reduced_f32_for_fp32_weight
        # on x86, for fp32, mkl should be enabled.
        # on aarch64, use mkldnn op for fp32 as well if acl is enabled
        if (
            not compute_with_lp
            and not mkldnn._is_mkldnn_acl_supported()
            and not torch._C.has_mkl
        ):
            return False
        for meta_value in [input_meta_value, weight_meta_value]:
            if (
                meta_value is None
                or meta_value.device.type != "cpu"
                or meta_value.dim() != 2
            ):
                return False
        if weight_idx == 2:
            bias_meta_value = linear_node.args[0].meta.get("val")
            if (
                bias_meta_value is None
                or meta_value.device.type != "cpu"
                or bias_meta_value.dim() != 1
                or bias_meta_value.size(0) != weight_meta_value.size(1)
            ):
                return False

        device_type = input_meta_value.device.type
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
        return True