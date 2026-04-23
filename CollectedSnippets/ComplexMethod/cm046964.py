def get_peft_model(
        model,
        r = 16,
        target_modules = None,
        lora_alpha = 16,
        lora_dropout = 0.0,
        bias = "none",
        finetune_vision_layers = True,
        finetune_language_layers = True,
        finetune_attention_modules = True,
        finetune_mlp_modules = True,
        layers_to_transform = None,
        layers_pattern = None,
        use_gradient_checkpointing = "unsloth",
        random_state = 3407,
        max_seq_length = 2048,  # not used anymore
        use_rslora = False,
        modules_to_save = None,
        init_lora_weights = True,
        loftq_config = {},
        task_type = TaskType.CAUSAL_LM,
        temporary_location = "_unsloth_temporary_saved_buffers",
        qat_scheme = None,
        target_parameters = None,  # For MoE expert layers (nn.Parameter)
        ensure_weight_tying = False,  # [TODO] Add `ensure_weight_tying` for `modules_to_save` for vision models
        **kwargs,
    ):
        if os.environ.get("UNSLOTH_ENABLE_FULL_FINETUNING", "0") == "1":
            print(
                "Unsloth: Full finetuning is enabled, so .get_peft_model has no effect"
            )
            return model
        transformers_set_seed(random_state)

        if type(r) is not int:
            raise TypeError(f"Unsloth: Rank of {str(r)} must be an integer.")
        if r <= 0:
            raise TypeError(f"Unsloth: Rank of {str(r)} must be larger than 0.")

        if isinstance(model, PeftModelForCausalLM):
            raise RuntimeError(
                "Unsloth: You already added LoRA adapters to your model!"
            )

        if target_modules == "all-linear":
            finetune_vision_layers = True
            finetune_language_layers = True
            finetune_attention_modules = True
            finetune_mlp_modules = True
        if target_modules is None or target_modules == "all-linear":
            target_modules = get_peft_regex(
                model,
                finetune_vision_layers = finetune_vision_layers,
                finetune_language_layers = finetune_language_layers,
                finetune_attention_modules = finetune_attention_modules,
                finetune_mlp_modules = finetune_mlp_modules,
            )
        else:
            assert type(target_modules) in (
                list,
                tuple,
                str,
            )

        if hasattr(model, "vllm_engine"):
            if (
                hasattr(model.vllm_engine, "llm_engine")
                and hasattr(model.vllm_engine.llm_engine, "vllm_config")
                and getattr(
                    model.vllm_engine.llm_engine.vllm_config, "lora_config", None
                )
                is None
            ):
                # If vLLM is being used but lora is not enabled, throw an error
                # Ref https://github.com/vllm-project/vllm/blob/51ba839555a5d122eadd91e9c16463ac288f5fa1/vllm/v1/engine/processor.py#L148-L151
                raise RuntimeError("Unsloth: LoRA is not enabled for this model!")
            if finetune_vision_layers:
                # vLLM does not support LoRA on vision layers
                # https://github.com/vllm-project/vllm/blob/main/vllm/lora/models.py#L471-L477
                # TODO: Update this once vLLM V1 supports LoRA on vision layers (possibly not happening)
                raise RuntimeError(
                    "Unsloth: Finetuning vision layers is not supported for fast_inference. Only text layers are supported!"
                )
            if model.config.model_type in VLLM_NON_LORA_VLM:
                # mllama is still only in vllm v0 https://arc.net/l/quote/llwkfgmu
                # https://docs.vllm.ai/en/stable/models/supported_models.html#text-generation_1
                # vLLM V0 does not support LoRA on multi modal models.
                # TODO: Update this once vLLM V1 supports Llama 3.2 aka mllama
                raise RuntimeError(
                    "Unsloth: LoRA finetuning for Llama 3.2 aka mllama models is not supported with fast_inference!"
                )

        # Clear deleted GPU items
        for _ in range(3):
            gc.collect()
            if DEVICE_TYPE in ("cuda", "hip"):
                torch.cuda.empty_cache()
            elif DEVICE_TYPE == "xpu":
                torch.xpu.empty_cache()
        max_seq_length = model.max_seq_length
        # If we pass loftq_config = None we will get an error
        loftq_config = validate_loftq_config(
            loftq_config, lora_dropout, bias, init_lora_weights, model
        )

        # Auto-detect MoE models and populate target_parameters for expert layers
        if target_parameters is None:
            target_parameters = get_moe_target_parameters(model, target_modules)

        # Get only allowed parameters for LoraConfig
        local_variables = {
            **locals(),
            **kwargs,
        }
        del local_variables["kwargs"]
        allowed_parameters = inspect.signature(LoraConfig).parameters.keys()
        lora_config = LoraConfig(
            **{k: v for k, v in local_variables.items() if k in allowed_parameters},
        )
        model = prepare_model_for_kbit_training(
            model,
            use_gradient_checkpointing = use_gradient_checkpointing,
        )
        # Gemma4 ClippableLinear wraps nn.Linear -- PEFT can't inject LoRA on it directly.
        # Monkey-patch PEFT to target the inner .linear child instead.
        _clippable_linear_cls = None
        try:
            from transformers.models.gemma4.modeling_gemma4 import (
                Gemma4ClippableLinear as _clippable_linear_cls,
            )
        except ImportError:
            pass
        if _clippable_linear_cls is not None:
            from peft.tuners.lora.model import LoraModel as _LoraModel

            _original_car = _LoraModel._create_and_replace

            def _patched_car(
                self,
                peft_config,
                adapter_name,
                target,
                target_name,
                parent,
                current_key = None,
                **kwargs,
            ):
                if isinstance(target, _clippable_linear_cls):
                    return _original_car(
                        self,
                        peft_config,
                        adapter_name,
                        target.linear,
                        "linear",
                        target,
                        current_key = current_key,
                        **kwargs,
                    )
                return _original_car(
                    self,
                    peft_config,
                    adapter_name,
                    target,
                    target_name,
                    parent,
                    current_key = current_key,
                    **kwargs,
                )

            _LoraModel._create_and_replace = _patched_car

        model = _get_peft_model(model, lora_config)

        # Restore original PEFT method
        if _clippable_linear_cls is not None:
            _LoraModel._create_and_replace = _original_car
        # Apply QAT + LoRA if specified
        if qat_scheme is not None:
            print("Unsloth: Applying QAT to mitigate quantization degradation")
            model = _prepare_model_for_qat(model, qat_scheme)
        # Fix LoraConfig.auto_mapping is None
        fix_lora_auto_mapping(model)
        # Enable gradients on modules which are trainable
        requires_grad_for_gradient_checkpointing(model)
        trust_remote_code = getattr(model, "_unsloth_trust_remote_code", False)
        model = FastBaseModel.post_patch_model(
            model,
            use_gradient_checkpointing = use_gradient_checkpointing,
            trust_remote_code = trust_remote_code,
        )
        model.max_seq_length = max_seq_length
        # Save to modules as well
        for module in model.modules():
            module.max_seq_length = max_seq_length
        # Clear deleted GPU items
        for _ in range(3):
            gc.collect()
            if DEVICE_TYPE in ("cuda", "hip"):
                torch.cuda.empty_cache()
            elif DEVICE_TYPE == "xpu":
                torch.xpu.empty_cache()
        patch_saving_functions(model, vision = True)
        patch_peft_fast_inference(model)

        # Add for_inference and for_training
        model.for_training = functools.partial(FastBaseModel.for_training, model)
        model.for_inference = functools.partial(FastBaseModel.for_inference, model)
        m = model
        while hasattr(m, "model"):
            m.for_training = functools.partial(FastBaseModel.for_training, m)
            m.for_inference = functools.partial(FastBaseModel.for_inference, m)
            m = m.model
        return model