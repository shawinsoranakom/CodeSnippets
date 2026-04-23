def _get_scheme_from_config(
        self, config: dict[str, Any], dynamic_mxfp4_quant: bool = False
    ) -> "QuarkScheme":
        if config.get("output_tensors") or config.get("bias"):
            raise NotImplementedError(
                "Currently, Quark models with output_tensors "
                "and bias quantized are not supported"
            )
        weight_config = cast(dict[str, Any], config.get("weight"))
        input_config = cast(dict[str, Any], config.get("input_tensors"))

        if self._is_fp8_w8a8(weight_config, input_config):
            is_fp8_w8a8_supported = self._check_scheme_supported(
                QuarkW8A8Fp8.get_min_capability(), error=False
            )
            if is_fp8_w8a8_supported:
                return QuarkW8A8Fp8(weight_config, input_config)
        elif self._is_static_tensor_w8a8(weight_config, input_config):
            weight_qscheme = cast(str, weight_config.get("qscheme"))
            return QuarkW8A8Int8(
                qscheme=weight_qscheme,
                is_static_input_scheme=True,
                input_symmetric=input_config.get("symmetric"),
            )
        elif self._is_w4a8_mxfp4_fp8(weight_config, input_config):
            is_w4a8_supported = self._check_scheme_supported(
                QuarkW4A8_MXFP4_FP8.get_min_capability(), error=False
            )
            if is_w4a8_supported:
                return QuarkW4A8_MXFP4_FP8(weight_config, input_config)
        elif self._is_dynamic_per_token_w8a8(weight_config, input_config):
            weight_qscheme = cast(str, weight_config.get("qscheme"))
            return QuarkW8A8Int8(
                qscheme=weight_qscheme,
                is_static_input_scheme=False,
                input_symmetric=input_config.get("symmetric"),
            )
        elif self._is_w_ocp_mx_a_x(weight_config, input_config):
            return QuarkOCP_MX(
                weight_config, input_config, dynamic_mxfp4_quant=dynamic_mxfp4_quant
            )

        raise NotImplementedError(
            "No quark compatible scheme was found. "
            f"Weight config: {weight_config}, "
            f"Input config: {input_config}"
        )