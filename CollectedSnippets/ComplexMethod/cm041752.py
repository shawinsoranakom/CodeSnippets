def get_train_args(args: dict[str, Any] | list[str] | None = None) -> _TRAIN_CLS:
    if is_env_enabled("USE_MCA"):
        model_args, data_args, training_args, finetuning_args, generating_args = _parse_train_mca_args(args)
    else:
        model_args, data_args, training_args, finetuning_args, generating_args = _parse_train_args(args)
        finetuning_args.use_mca = False

    # Setup logging
    if training_args.should_log:
        _set_transformers_logging()

    # Check arguments
    if finetuning_args.stage != "sft":
        if training_args.predict_with_generate:
            raise ValueError("`predict_with_generate` cannot be set as True except SFT.")

        if data_args.neat_packing:
            raise ValueError("`neat_packing` cannot be set as True except SFT.")

        if data_args.train_on_prompt or data_args.mask_history:
            raise ValueError("`train_on_prompt` or `mask_history` cannot be set as True except SFT.")

    if finetuning_args.stage == "sft" and training_args.do_predict and not training_args.predict_with_generate:
        raise ValueError("Please enable `predict_with_generate` to save model predictions.")

    if finetuning_args.stage in ["rm", "ppo"] and training_args.load_best_model_at_end:
        raise ValueError("RM and PPO stages do not support `load_best_model_at_end`.")

    if finetuning_args.stage == "ppo":
        if not training_args.do_train:
            raise ValueError("PPO training does not support evaluation, use the SFT stage to evaluate models.")

        if model_args.shift_attn:
            raise ValueError("PPO training is incompatible with S^2-Attn.")

        if finetuning_args.reward_model_type == "lora" and model_args.use_kt:
            raise ValueError("KTransformers does not support lora reward model.")

        if finetuning_args.reward_model_type == "lora" and model_args.use_unsloth:
            raise ValueError("Unsloth does not support lora reward model.")

        if training_args.report_to and any(
            logger not in ("wandb", "tensorboard", "trackio", "none") for logger in training_args.report_to
        ):
            raise ValueError("PPO only accepts wandb, tensorboard, or trackio logger.")

    if not model_args.use_kt and training_args.parallel_mode == ParallelMode.NOT_DISTRIBUTED:
        raise ValueError("Please launch distributed training with `llamafactory-cli` or `torchrun`.")

    if training_args.deepspeed and training_args.parallel_mode != ParallelMode.DISTRIBUTED:
        raise ValueError("Please use `FORCE_TORCHRUN=1` to launch DeepSpeed training.")

    if training_args.max_steps == -1 and data_args.streaming:
        raise ValueError("Please specify `max_steps` in streaming mode.")

    if training_args.do_train and data_args.dataset is None:
        raise ValueError("Please specify dataset for training.")

    if (training_args.do_eval or training_args.do_predict or training_args.predict_with_generate) and (
        data_args.eval_dataset is None and data_args.val_size < 1e-6
    ):
        raise ValueError("Please make sure eval_dataset be provided or val_size >1e-6")

    if training_args.predict_with_generate:
        if is_deepspeed_zero3_enabled():
            raise ValueError("`predict_with_generate` is incompatible with DeepSpeed ZeRO-3.")

        if finetuning_args.compute_accuracy:
            raise ValueError("Cannot use `predict_with_generate` and `compute_accuracy` together.")

    if training_args.do_train and model_args.quantization_device_map == "auto":
        raise ValueError("Cannot use device map for quantized models in training.")

    if finetuning_args.pissa_init and is_deepspeed_zero3_enabled():
        raise ValueError("Please use scripts/pissa_init.py to initialize PiSSA in DeepSpeed ZeRO-3.")

    if finetuning_args.pure_bf16:
        if not (is_torch_bf16_gpu_available() or (is_torch_npu_available() and torch.npu.is_bf16_supported())):
            raise ValueError("This device does not support `pure_bf16`.")

        if is_deepspeed_zero3_enabled():
            raise ValueError("`pure_bf16` is incompatible with DeepSpeed ZeRO-3.")

    if training_args.parallel_mode == ParallelMode.DISTRIBUTED:
        if finetuning_args.use_galore and finetuning_args.galore_layerwise:
            raise ValueError("Distributed training does not support layer-wise GaLore.")

        if finetuning_args.use_apollo and finetuning_args.apollo_layerwise:
            raise ValueError("Distributed training does not support layer-wise APOLLO.")

        if finetuning_args.use_badam:
            if finetuning_args.badam_mode == "ratio":
                raise ValueError("Radio-based BAdam does not yet support distributed training, use layer-wise BAdam.")
            elif not is_deepspeed_zero3_enabled():
                raise ValueError("Layer-wise BAdam only supports DeepSpeed ZeRO-3 training.")

    if training_args.deepspeed is not None and (finetuning_args.use_galore or finetuning_args.use_apollo):
        raise ValueError("GaLore and APOLLO are incompatible with DeepSpeed yet.")

    if not finetuning_args.use_mca and training_args.fp8 and model_args.quantization_bit is not None:
        raise ValueError("FP8 training is not compatible with quantization. Please disable one of them.")

    if model_args.infer_backend != EngineName.HF:
        raise ValueError("vLLM/SGLang backend is only available for API, CLI and Web.")

    if model_args.use_unsloth and is_deepspeed_zero3_enabled():
        raise ValueError("Unsloth is incompatible with DeepSpeed ZeRO-3.")

    if model_args.use_kt and is_deepspeed_zero3_enabled():
        raise ValueError("KTransformers is incompatible with DeepSpeed ZeRO-3.")

    _set_env_vars()
    _verify_model_args(model_args, data_args, finetuning_args)
    _check_extra_dependencies(model_args, finetuning_args, training_args)
    _verify_trackio_args(training_args)

    if not finetuning_args.use_mca and training_args.fp8_enable_fsdp_float8_all_gather and not training_args.fp8:
        logger.warning_rank0("fp8_enable_fsdp_float8_all_gather requires fp8=True. Setting fp8=True.")
        model_args.fp8 = True

    if (
        training_args.do_train
        and finetuning_args.finetuning_type == "lora"
        and model_args.quantization_bit is None
        and model_args.resize_vocab
        and finetuning_args.additional_target is None
    ):
        logger.warning_rank0(
            "Remember to add embedding layers to `additional_target` to make the added tokens trainable."
        )

    if training_args.do_train and model_args.quantization_bit is not None and (not model_args.upcast_layernorm):
        logger.warning_rank0("We recommend enable `upcast_layernorm` in quantized training.")

    if training_args.do_train and (not training_args.fp16) and (not training_args.bf16):
        logger.warning_rank0("We recommend enable mixed precision training.")

    if (
        training_args.do_train
        and (finetuning_args.use_galore or finetuning_args.use_apollo)
        and not finetuning_args.pure_bf16
    ):
        logger.warning_rank0(
            "Using GaLore or APOLLO with mixed precision training may significantly increases GPU memory usage."
        )

    if (not training_args.do_train) and model_args.quantization_bit is not None:
        logger.warning_rank0("Evaluating model in 4/8-bit mode may cause lower scores.")

    if (not training_args.do_train) and finetuning_args.stage == "dpo" and finetuning_args.ref_model is None:
        logger.warning_rank0("Specify `ref_model` for computing rewards at evaluation.")

    # Post-process training arguments
    training_args.generation_max_length = training_args.generation_max_length or data_args.cutoff_len
    training_args.generation_num_beams = data_args.eval_num_beams or training_args.generation_num_beams
    training_args.remove_unused_columns = False  # important for multimodal dataset

    if finetuning_args.finetuning_type == "lora":
        # https://github.com/huggingface/transformers/blob/v4.50.0/src/transformers/trainer.py#L782
        training_args.label_names = training_args.label_names or ["labels"]

    if "swanlab" in training_args.report_to and finetuning_args.use_swanlab:
        training_args.report_to.remove("swanlab")

    if (
        training_args.parallel_mode == ParallelMode.DISTRIBUTED
        and training_args.ddp_find_unused_parameters is None
        and finetuning_args.finetuning_type == "lora"
    ):
        logger.info_rank0("Set `ddp_find_unused_parameters` to False in DDP training since LoRA is enabled.")
        training_args.ddp_find_unused_parameters = False

    if finetuning_args.stage in ["rm", "ppo"] and finetuning_args.finetuning_type in ["full", "freeze"]:
        can_resume_from_checkpoint = False
        if training_args.resume_from_checkpoint is not None:
            logger.warning_rank0("Cannot resume from checkpoint in current stage.")
            training_args.resume_from_checkpoint = None
    else:
        can_resume_from_checkpoint = True

    if (
        training_args.resume_from_checkpoint is None
        and training_args.do_train
        and os.path.isdir(training_args.output_dir)
        and not getattr(training_args, "overwrite_output_dir", False) # for mca training args and transformers >= 5.0
        and can_resume_from_checkpoint
    ):
        last_checkpoint = get_last_checkpoint(training_args.output_dir)
        if last_checkpoint is None and any(
            os.path.isfile(os.path.join(training_args.output_dir, name)) for name in CHECKPOINT_NAMES
        ):
            raise ValueError("Output directory already exists and is not empty. Please set `overwrite_output_dir`.")

        if last_checkpoint is not None:
            training_args.resume_from_checkpoint = last_checkpoint
            logger.info_rank0(f"Resuming training from {training_args.resume_from_checkpoint}.")
            logger.info_rank0("Change `output_dir` or use `overwrite_output_dir` to avoid.")

    if (
        finetuning_args.stage in ["rm", "ppo"]
        and finetuning_args.finetuning_type == "lora"
        and training_args.resume_from_checkpoint is not None
    ):
        logger.warning_rank0(
            f"Add {training_args.resume_from_checkpoint} to `adapter_name_or_path` to resume training from checkpoint."
        )

    # Post-process model arguments
    if training_args.bf16 or finetuning_args.pure_bf16:
        model_args.compute_dtype = torch.bfloat16
    elif training_args.fp16:
        model_args.compute_dtype = torch.float16

    model_args.device_map = {"": get_current_device()}
    model_args.model_max_length = data_args.cutoff_len
    model_args.block_diag_attn = data_args.neat_packing
    data_args.packing = data_args.packing if data_args.packing is not None else finetuning_args.stage == "pt"

    # Log on each process the small summary
    logger.info(
        f"Process rank: {training_args.process_index}, "
        f"world size: {training_args.world_size}, device: {training_args.device}, "
        f"distributed training: {training_args.parallel_mode == ParallelMode.DISTRIBUTED}, "
        f"compute dtype: {str(model_args.compute_dtype)}"
    )
    transformers.set_seed(training_args.seed)

    return model_args, data_args, training_args, finetuning_args, generating_args