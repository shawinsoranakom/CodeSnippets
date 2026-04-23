def get_moe_method(
        quant_config: "QuarkConfig",  # type: ignore # noqa E501 # noqa F821
        module: torch.nn.Module,
        layer_name: str,
    ) -> "QuarkMoEMethod":
        layer_quant_config = quant_config._find_matched_config(layer_name, module)

        if layer_quant_config.get("output_tensors") or layer_quant_config.get("bias"):
            raise NotImplementedError(
                "Currently, Quark models with "
                "output_tensors and bias "
                "quantized are not supported"
            )

        weight_config = layer_quant_config.get("weight")
        input_config = layer_quant_config.get("input_tensors")

        if quant_config._is_fp8_w4a8(weight_config, input_config):
            return QuarkW4A8Fp8MoEMethod(weight_config, input_config, module.moe_config)
        elif quant_config._is_fp8_w8a8(weight_config, input_config):
            return QuarkW8A8Fp8MoEMethod(weight_config, input_config, module.moe_config)
        elif quant_config._is_w_ocp_mx_a_x(weight_config, input_config):
            emulate = not current_platform.supports_mx() or not (
                rocm_aiter_ops.is_fused_moe_enabled()
            )
            if (
                input_config is not None
                and input_config.get("dtype") == "fp8_e4m3"
                and not input_config.get("is_dynamic")
                and not emulate
            ):
                return QuarkOCP_MX_MoEMethod_OSS(
                    weight_config, input_config, module.moe_config
                )
            else:
                return QuarkOCP_MX_MoEMethod(
                    weight_config, input_config, module.moe_config
                )
        elif quant_config._is_static_tensor_w8a8(
            weight_config, input_config
        ) or quant_config._is_dynamic_per_token_w8a8(weight_config, input_config):
            return QuarkW8A8Int8MoEMethod(
                weight_config, input_config, module.moe_config
            )
        else:
            raise RuntimeError("Unsupported FusedMoe scheme")