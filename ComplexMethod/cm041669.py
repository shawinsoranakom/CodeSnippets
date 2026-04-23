def configure_moe(config: "PretrainedConfig", model_args: "ModelArguments", is_trainable: bool) -> None:
    if not is_trainable or not model_args.moe_aux_loss_coef:
        return

    model_type = getattr(config, "model_type", None)
    text_config = getattr(config, "text_config", None)  # for multimodal model

    if model_type in [
        "dbrx",
        "ernie4_5_moe",
        "granitemoe",
        "jamba",
        "jetmoe",
        "llama4",
        "mixtral",
        "olmoe",
        "phimoe",
        "qwen2_moe",
        "qwen3_moe",
    ]:
        setattr(config, "output_router_logits", True)

    if text_config and getattr(text_config, "model_type", None) in [
        "glm4v_moe_text",  # glmv4_5
        "qwen3_moe",  # internvl_3_5
    ]:
        setattr(text_config, "output_router_logits", True)

    if model_type in [
        "ernie4_5_moe",
        "granitemoe",
        "jamba",
        "llama4",
        "mixtral",
        "olmoe",
        "phimoe",
        "qwen2_moe",
        "qwen3_moe",
    ]:
        setattr(config, "router_aux_loss_coef", model_args.moe_aux_loss_coef)

    elif text_config and getattr(text_config, "model_type", None) in ["qwen3_moe"]:
        setattr(text_config, "router_aux_loss_coef", model_args.moe_aux_loss_coef)

    elif model_type == "deepseek":
        setattr(config, "aux_loss_alpha", model_args.moe_aux_loss_coef)

    elif model_type == "jetmoe":
        setattr(config, "aux_loss_coef", model_args.moe_aux_loss_coef)