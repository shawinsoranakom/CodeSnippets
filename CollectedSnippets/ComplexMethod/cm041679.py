def prepare_model_for_training(model: "PreTrainedModel", model_args: "ModelArguments") -> None:
    r"""Prepare the model before training.

    Include:
    (1) cast the layernorm in fp32
    (2) make output embedding layer require grads
    (3) add the upcasting of the lm_head in fp32.
    """
    if model_args.upcast_layernorm:
        logger.info_rank0("Upcasting layernorm weights in float32.")
        for name, param in model.named_parameters():
            if param.ndim == 1 and any(ln_name in name for ln_name in LAYERNORM_NAMES):
                param.data = param.data.to(torch.float32)

    if (
        os.environ.get("ACCELERATE_USE_FSDP", "false").lower() == "true"
        and int(os.environ.get("FSDP_VERSION", "1")) == 2
    ):
        model_args.use_reentrant_gc = False
        logger.warning_rank0("You are using fsdp2, `use_reentrant_gc` has been set to False.")

    if not model_args.disable_gradient_checkpointing:
        if not getattr(model, "supports_gradient_checkpointing", False):
            logger.warning_rank0("Current model does not support gradient checkpointing.")
        else:
            # use_reentrant=False might increase VRAM usage (have not been empirically verified yet)
            # According to: https://github.com/huggingface/transformers/issues/28339
            gradient_checkpointing_enable = partial(
                _gradient_checkpointing_enable, use_unsloth_gc=model_args.use_unsloth_gc
            )
            model.gradient_checkpointing_enable = MethodType(gradient_checkpointing_enable, model)
            model.gradient_checkpointing_enable(
                gradient_checkpointing_kwargs={"use_reentrant": model_args.use_reentrant_gc}
            )
            setattr(model.config, "use_cache", False)  # turn off when gradient checkpointing is enabled
            logger.info_rank0("Gradient checkpointing enabled.")

    if model_args.upcast_lmhead_output:
        output_layer = model.get_output_embeddings()
        if isinstance(output_layer, torch.nn.Linear) and output_layer.weight.dtype != torch.float32:
            logger.info_rank0("Upcasting lm_head outputs in float32.")
            output_layer.register_forward_hook(_fp32_forward_post_hook)