def configure_attn_implementation(config: "PretrainedConfig", model_args: "ModelArguments") -> None:
    from transformers.utils import is_flash_attn_2_available

    if getattr(config, "model_type", None) == "gpt_oss":
        from transformers.integrations.hub_kernels import load_and_register_kernel

        flash_attn3_kernel = "kernels-community/vllm-flash-attn3"
        load_and_register_kernel(flash_attn3_kernel)
        setattr(config, "_attn_implementation", flash_attn3_kernel)
        setattr(config, "_attn_implementation_internal", flash_attn3_kernel)
        model_args.flash_attn = AttentionFunction.FA3

        logger.info_rank0("Using FlashAttention-3 with attention sink for the gpt-oss model.")
        return

    if getattr(config, "model_type", None) == "gemma2":
        if model_args.flash_attn == AttentionFunction.AUTO or model_args.flash_attn == AttentionFunction.FA2:
            if is_flash_attn_2_available():
                if model_args.flash_attn != AttentionFunction.FA2:
                    logger.warning_rank0("Gemma 2 should use flash attention 2, change `flash_attn` to fa2.")
                    model_args.flash_attn = AttentionFunction.FA2
            else:
                logger.warning_rank0("FlashAttention-2 is not installed, use eager attention.")
                model_args.flash_attn = AttentionFunction.DISABLED
        elif model_args.flash_attn == AttentionFunction.SDPA:
            logger.warning_rank0(
                "Gemma-2 should use soft-capping attention, while the SDPA attention does not support it."
            )

    if getattr(config, "model_type", None) in ["youtu", "youtu_vl"]:
        if model_args.flash_attn in (AttentionFunction.AUTO, AttentionFunction.SDPA):
            logger.warning_rank0("Youtu-VL does not support SDPA, forcing eager attention.")
            model_args.flash_attn = AttentionFunction.DISABLED

    if model_args.flash_attn == AttentionFunction.AUTO:
        return

    elif model_args.flash_attn == AttentionFunction.DISABLED:
        requested_attn_implementation = "eager"

    elif model_args.flash_attn == AttentionFunction.SDPA:
        if not is_torch_version_greater_than("2.1.1"):
            logger.warning_rank0("torch>=2.1.1 is required for SDPA attention.")
            return

        requested_attn_implementation = "sdpa"
    elif model_args.flash_attn == AttentionFunction.FA2:
        from transformers import is_torch_npu_available

        if not (is_flash_attn_2_available() or is_torch_npu_available()):
            logger.warning_rank0("FlashAttention-2 is not installed.")
            return

        requested_attn_implementation = "flash_attention_2"
    else:
        raise NotImplementedError(f"Unknown attention type: {model_args.flash_attn}")

    if getattr(config, "model_type", None) == "internlm2":  # special case for custom models
        setattr(config, "attn_implementation", requested_attn_implementation)
    elif getattr(config, "model_type", None) == "kimi_vl":
        setattr(config.vision_config, "_attn_implementation", requested_attn_implementation)
        setattr(config.text_config, "_attn_implementation", requested_attn_implementation)
    elif getattr(config, "model_type", None) == "youtu_vl":
        setattr(config, "attn_implementation", requested_attn_implementation)
        setattr(config, "_attn_implementation", requested_attn_implementation)
        if hasattr(config, "vision_config"):
            setattr(config.vision_config, "_attn_implementation", requested_attn_implementation)
        if hasattr(config, "text_config"):
            setattr(config.text_config, "_attn_implementation", requested_attn_implementation)
    else:
        setattr(config, "_attn_implementation", requested_attn_implementation)