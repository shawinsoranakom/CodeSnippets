def _is_w4a8_mxfp4_fp8(
        self,
        weight_quant: dict[str, Any] | None,
        input_quant: dict[str, Any] | None,
    ) -> bool:
        if weight_quant is None or input_quant is None:
            return False

        is_weight_mxfp4 = (
            weight_quant.get("dtype") == "fp4"
            and weight_quant.get("qscheme") == "per_group"
            and weight_quant.get("group_size") == 32
            and weight_quant.get("scale_format") == "e8m0"
            and not weight_quant.get("is_dynamic")
        )

        is_input_fp8 = (
            input_quant.get("dtype") == "fp8_e4m3"
            and input_quant.get("qscheme") == "per_tensor"
            and not input_quant.get("is_dynamic")  # Static per-tensor
            and input_quant.get("symmetric") is True  # Symmetric quantization
        )

        return is_weight_mxfp4 and is_input_fp8