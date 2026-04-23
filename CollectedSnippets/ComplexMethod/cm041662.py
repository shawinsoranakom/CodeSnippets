def _setup_lora_tuning(
    config: "PretrainedConfig",
    model: "PreTrainedModel",
    model_args: "ModelArguments",
    finetuning_args: "FinetuningArguments",
    is_trainable: bool,
    cast_trainable_params_to_fp32: bool,
) -> "PeftModel":
    if is_trainable:
        if finetuning_args.finetuning_type == "oft":
            logger.info_rank0("Fine-tuning method: OFT")
        else:
            logger.info_rank0("Fine-tuning method: {}".format("DoRA" if finetuning_args.use_dora else "LoRA"))

    adapter_to_resume = None

    if model_args.adapter_name_or_path is not None:
        is_mergeable = True
        if getattr(model, "quantization_method", None):  # merge lora in quantized model is unstable
            assert len(model_args.adapter_name_or_path) == 1, "Quantized model only accepts a single adapter."
            is_mergeable = False

        if is_deepspeed_zero3_enabled():
            assert len(model_args.adapter_name_or_path) == 1, "Cannot use multiple adapters in DeepSpeed ZeRO-3."
            is_mergeable = False

        if model_args.use_kt:
            assert len(model_args.adapter_name_or_path) == 1, "KTransformers model only accepts a single adapter"
            is_mergeable = False

        if model_args.use_unsloth:
            assert len(model_args.adapter_name_or_path) == 1, "Unsloth model only accepts a single adapter."
            is_mergeable = False

        if (is_trainable and not finetuning_args.create_new_adapter) or (not is_mergeable):
            adapter_to_merge = model_args.adapter_name_or_path[:-1]
            adapter_to_resume = model_args.adapter_name_or_path[-1]
        else:
            adapter_to_merge = model_args.adapter_name_or_path

        init_kwargs = {
            "subfolder": model_args.adapter_folder,
            "offload_folder": model_args.offload_folder,
            "cache_dir": model_args.cache_dir,
            "revision": model_args.model_revision,
            "token": model_args.hf_hub_token,
        }

        if model_args.use_kt:
            if model_args.infer_backend != EngineName.KT:
                raise ValueError(
                    "We should use ktransformers as backend to infer the adapter fine-tuned by ktransformers."
                )

        for adapter in adapter_to_merge:
            model: LoraModel = PeftModel.from_pretrained(model, adapter, **init_kwargs)
            model = model.merge_and_unload()

        if len(adapter_to_merge) > 0:
            logger.info_rank0(f"Merged {len(adapter_to_merge)} adapter(s).")

        if adapter_to_resume is not None:  # resume lora training
            if model_args.use_kt:
                model = load_kt_peft_model(model_args, model)
            elif model_args.use_unsloth:
                model = load_unsloth_peft_model(config, model_args, finetuning_args, is_trainable=is_trainable)
            else:
                model = PeftModel.from_pretrained(model, adapter_to_resume, is_trainable=is_trainable, **init_kwargs)

        logger.info_rank0("Loaded adapter(s): {}".format(",".join(model_args.adapter_name_or_path)))

    if is_trainable and adapter_to_resume is None:  # create new lora weights while training
        if len(finetuning_args.lora_target) == 1 and finetuning_args.lora_target[0] == "all":
            target_modules = find_all_linear_modules(model, finetuning_args.freeze_vision_tower)
        else:
            target_modules = finetuning_args.lora_target

        if model_args.use_kt:
            new_list = []
            for m in target_modules:
                if m in ("down_proj", "up_proj", "gate_proj"):
                    new_list.extend([f"mlp.{m}", f"shared_experts.{m}"])
                elif m not in ("generate_linear", "orig_module", "prefill_linear"):
                    new_list.append(m)

            target_modules[:] = new_list

        if finetuning_args.use_llama_pro:
            target_modules = find_expanded_modules(model, target_modules, finetuning_args.freeze_trainable_layers)

        target_modules = patch_target_modules(model, finetuning_args, target_modules)

        if (
            finetuning_args.use_dora
            and getattr(model, "quantization_method", None) is not None
            and getattr(model, "quantization_method", None) != QuantizationMethod.BNB
        ):
            raise ValueError("DoRA is not compatible with PTQ-quantized models.")

        if model_args.resize_vocab and finetuning_args.additional_target is None:
            input_embeddings = model.get_input_embeddings()
            output_embeddings = model.get_output_embeddings()
            module_names = set()
            for name, module in model.named_modules():
                if module in [input_embeddings, output_embeddings]:
                    module_names.add(name.split(".")[-1])

            finetuning_args.additional_target = module_names
            logger.warning_rank0("Vocab has been resized, add {} to trainable params.".format(",".join(module_names)))

        if finetuning_args.finetuning_type == "lora":
            peft_kwargs = {
                "r": finetuning_args.lora_rank,
                "target_modules": target_modules,
                "lora_alpha": finetuning_args.lora_alpha,
                "lora_dropout": finetuning_args.lora_dropout,
                "use_rslora": finetuning_args.use_rslora,
                "use_dora": finetuning_args.use_dora,
                "modules_to_save": finetuning_args.additional_target,
            }
        elif finetuning_args.finetuning_type == "oft":
            peft_kwargs = {
                "r": finetuning_args.oft_rank,
                "oft_block_size": finetuning_args.oft_block_size,
                "target_modules": target_modules,
                "module_dropout": finetuning_args.module_dropout,
                "modules_to_save": finetuning_args.additional_target,
            }

        if model_args.use_kt:
            if finetuning_args.finetuning_type == "oft":
                raise ValueError("KTransformers is currently not supported for OFT.")
            if finetuning_args.finetuning_type == "lora":
                peft_config = LoraConfig(
                    task_type=TaskType.CAUSAL_LM,
                    inference_mode=False,
                    **peft_kwargs,
                )
            else:
                raise ValueError("KTransformers is currently only supported for LoRA.")

            model = get_kt_peft_model(model, peft_config)
            print(f"KT_model:{model}")
        elif model_args.use_unsloth:
            if finetuning_args.finetuning_type == "oft":
                raise ValueError("Unsloth is currently not supported for OFT.")

            model = get_unsloth_peft_model(model, model_args, peft_kwargs)
        else:
            if finetuning_args.pissa_init:
                if finetuning_args.pissa_iter == -1:
                    logger.info_rank0("Using PiSSA initialization.")
                    peft_kwargs["init_lora_weights"] = "pissa"
                else:
                    logger.info_rank0(f"Using PiSSA initialization with FSVD steps {finetuning_args.pissa_iter}.")
                    peft_kwargs["init_lora_weights"] = f"pissa_niter_{finetuning_args.pissa_iter}"

            if finetuning_args.finetuning_type == "lora":
                peft_config = LoraConfig(
                    task_type=TaskType.CAUSAL_LM,
                    inference_mode=False,
                    **peft_kwargs,
                )
            elif finetuning_args.finetuning_type == "oft":
                peft_config = OFTConfig(
                    task_type=TaskType.CAUSAL_LM,
                    inference_mode=False,
                    **peft_kwargs,
                )
            model = get_peft_model(model, peft_config)

    if is_trainable and cast_trainable_params_to_fp32:
        for param in filter(lambda p: p.requires_grad, model.parameters()):
            param.data = param.data.to(torch.float32)

    return model