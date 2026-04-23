def is_supported_config(
        cls: type["FusedMoEExperts"],
        moe_config: FusedMoEConfig,
        weight_key: QuantKey | None,
        activation_key: QuantKey | None,
        activation_format: FusedMoEActivationFormat,
    ) -> tuple[bool, str | None]:
        def _make_reason(reason: str) -> str:
            return f"kernel does not support {reason}"

        if not cls._supports_current_device():
            return False, _make_reason(f"current device {current_platform.device_name}")
        elif not (moe_config.is_act_and_mul or cls._supports_no_act_and_mul()):
            return False, _make_reason("no act_and_mul MLP layer")
        elif not cls._supports_activation(moe_config.activation):
            return False, _make_reason(f"{moe_config.activation} activation")
        elif not cls._supports_quant_scheme(weight_key, activation_key):
            return False, _make_reason(
                f"quantization scheme {weight_key}x{activation_key}"
            )
        elif not cls._supports_parallel_config(moe_config.moe_parallel_config):
            return False, _make_reason(
                f"parallel config {moe_config.moe_parallel_config}"
            )
        elif not cls._supports_routing_method(
            moe_config.routing_method, weight_key, activation_key
        ):
            return False, _make_reason(f"routing method {moe_config.routing_method}")
        elif not cls._supports_router_logits_dtype(
            moe_config.router_logits_dtype,
            moe_config.routing_method,
        ):
            return False, _make_reason(
                f"router logits dtype {moe_config.router_logits_dtype}"
            )
        elif not cls._supports_shape(moe_config.hidden_dim):
            return False, _make_reason(
                f"{moe_config.hidden_dim} hidden dim is not supported"
            )
        elif activation_format != cls.activation_format():
            return False, _make_reason(f"{activation_format.value} activation format")
        elif envs.VLLM_BATCH_INVARIANT and not cls._supports_batch_invariance():
            return False, _make_reason("batch invariance")
        return True, None