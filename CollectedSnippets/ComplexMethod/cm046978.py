def patch_peft_model(
        model,
        use_gradient_checkpointing = "unsloth",
    ):
        if os.environ.get("UNSLOTH_USE_NEW_MODEL", "0") == "1":
            return FastBaseModel.patch_peft_model(
                model = model,
                use_gradient_checkpointing = use_gradient_checkpointing,
            )
        if not isinstance(model, PeftModelForCausalLM) and not isinstance(
            model, PeftModelForSequenceClassification
        ):
            raise TypeError(
                "Unsloth: Your model needs to call `.get_peft_model` first!"
            )

        # Get activation function
        model_type = model.config.model_type

        if model_type == "llama":
            apply_lora_mlp = apply_lora_mlp_swiglu
        elif model_type == "mistral":
            apply_lora_mlp = apply_lora_mlp_swiglu
        elif model_type == "qwen2":
            apply_lora_mlp = apply_lora_mlp_swiglu
        elif model_type == "gemma":
            apply_lora_mlp = apply_lora_mlp_geglu_approx
        elif model_type == "gemma2":
            apply_lora_mlp = apply_lora_mlp_geglu_approx
        elif model_type == "cohere":
            apply_lora_mlp = apply_lora_mlp_swiglu
        elif model_type == "granite":
            apply_lora_mlp = apply_lora_mlp_swiglu
        elif model_type == "qwen3":
            apply_lora_mlp = apply_lora_mlp_swiglu
        elif model_type == "falcon_h1":
            apply_lora_mlp = apply_lora_mlp_swiglu
        elif model_type == "qwen3moe":
            apply_lora_mlp = apply_lora_mlp_swiglu
        else:
            raise NotImplementedError(f"Unsloth: {model_type} is not yet implemented!")

        model = prepare_model_for_kbit_training(
            model,
            use_gradient_checkpointing = use_gradient_checkpointing,
            use_reentrant = True,
        )

        # Fix up config for transformers uploading PEFT
        for active_adapter in model.peft_config.keys():
            # Not necessary since we requires transformers >= 4.37
            if False:
                name = model.peft_config[active_adapter].base_model_name_or_path
                if name.startswith("unsloth/") and name.endswith("-bnb-4bit"):
                    name = name[: len(name) - len("-bnb-4bit")]
                    model.peft_config[active_adapter].base_model_name_or_path = name
                pass
            # Add revision to enable future fast inference paths
            # [TODO] Bugs out!see https://github.com/unslothai/unsloth/issues/492
            # model.peft_config[active_adapter].revision = f"unsloth"

        from transformers.trainer import Trainer

        if Trainer._inner_training_loop.__name__ != "_fast_inner_training_loop":
            raise RuntimeError(
                "Unsloth: Unsuccessfully patched Trainer! Please file a bug report!"
            )

        # Fix loftq issues
        # loftq_config must not = None, but rather {}
        all_configs = model.peft_config
        for key, current_config in all_configs.items():
            if (
                hasattr(current_config, "loftq_config")
                and current_config.loftq_config is None
            ):
                new_args = current_config.__dict__
                new_args["loftq_config"] = {}
                current_config = current_config.__class__(**new_args)
                all_configs[key] = current_config

        # Do patching
        n_mlp = 0
        n_qkv = 0
        n_o = 0

        active_adapter = (
            model.active_adapters[0]
            if hasattr(model, "active_adapters")
            else model.active_adapter
        )

        # Get dropout and bias
        lora_dropout = model.peft_config[active_adapter].lora_dropout
        bias = model.peft_config[active_adapter].bias

        # We also do not inplace edit QKV for Cohere!
        _apply_lora_mlp = (
            functools.partial(apply_lora_mlp, inplace = False)
            if model_type == "cohere"
            else apply_lora_mlp
        )

        if lora_dropout == 0 and bias == "none":
            for idx, layer in enumerate(model.model.model.layers):
                if model_type != "falcon_h1":
                    # LoRAMLP.apply doesn't have functionality for gate and down multipliers yet.
                    # Don't patch falcon h1 for the time being.

                    # MLP patching
                    mlp_module = layer.mlp
                    gate_proj = mlp_module.gate_proj
                    up_proj = mlp_module.up_proj
                    down_proj = mlp_module.down_proj

                    if (
                        hasattr(gate_proj, "lora_A")
                        and hasattr(up_proj, "lora_A")
                        and hasattr(down_proj, "lora_A")
                        and (getattr(gate_proj, "base_layer", gate_proj).bias is None)
                        and (getattr(up_proj, "base_layer", up_proj).bias is None)
                        and (getattr(down_proj, "base_layer", down_proj).bias is None)
                        and (
                            len(getattr(gate_proj, "lora_magnitude_vector", []) or [])
                            == 0
                        )
                        and (
                            len(getattr(up_proj, "lora_magnitude_vector", []) or [])
                            == 0
                        )
                        and (
                            len(getattr(down_proj, "lora_magnitude_vector", []) or [])
                            == 0
                        )
                    ):
                        # https://stackoverflow.com/questions/50599045/python-replacing-a-function-within-a-class-of-a-module
                        if hasattr(mlp_module, "_unsloth_forward"):
                            # then we've patched the mlp to use TiledMLP
                            mlp_module._unsloth_forward = types.MethodType(
                                _apply_lora_mlp, mlp_module
                            )
                        else:
                            mlp_module.forward = types.MethodType(
                                _apply_lora_mlp, mlp_module
                            )
                        n_mlp += 1
                    else:
                        logger.warning_once(
                            "Not an error, but Unsloth cannot patch MLP layers with our manual autograd engine since either LoRA adapters\n"
                            "are not enabled or a bias term (like in Qwen) is used."
                        )

                # QKV attention patching
                q_proj = layer.self_attn.q_proj
                k_proj = layer.self_attn.k_proj
                v_proj = layer.self_attn.v_proj
                if (
                    hasattr(q_proj, "lora_A")
                    and hasattr(k_proj, "lora_A")
                    and hasattr(v_proj, "lora_A")
                    and (getattr(q_proj, "base_layer", q_proj).bias is None)
                    and (getattr(k_proj, "base_layer", k_proj).bias is None)
                    and (getattr(v_proj, "base_layer", v_proj).bias is None)
                    and (len(getattr(q_proj, "lora_magnitude_vector", []) or []) == 0)
                    and (len(getattr(k_proj, "lora_magnitude_vector", []) or []) == 0)
                    and (len(getattr(v_proj, "lora_magnitude_vector", []) or []) == 0)
                ):
                    layer.self_attn.apply_qkv = apply_lora_qkv
                    n_qkv += 1
                else:
                    if model_type == "qwen2":
                        n_qkv += 1
                    else:
                        logger.warning_once(
                            "Not an error, but Unsloth cannot patch Attention layers with our manual autograd engine since either LoRA adapters\n"
                            "are not enabled or a bias term (like in Qwen) is used."
                        )

                # O attention patching
                o_proj = layer.self_attn.o_proj
                if (
                    hasattr(o_proj, "lora_A")
                    and (getattr(o_proj, "base_layer", o_proj).bias is None)
                    and (len(getattr(o_proj, "lora_magnitude_vector", []) or []) == 0)
                ):
                    layer.self_attn.apply_o = apply_lora_o
                    n_o += 1
                else:
                    logger.warning_once(
                        "Not an error, but Unsloth cannot patch O projection layer with our manual autograd engine since either LoRA adapters\n"
                        "are not enabled or a bias term (like in Qwen) is used."
                    )

        logger.warning_once(
            f"Unsloth {__version__} patched {len(model.model.model.layers)} layers with "
            f"{n_qkv} QKV layers, {n_o} O layers and {n_mlp} MLP layers.",
        )
        patch_saving_functions(model)

        # Patch cross entropy loss labels
        # Fixes https://github.com/unslothai/unsloth/issues/10
        max_seq_length = model.max_seq_length
        # extra_ignored_labels = torch.full((max_seq_length, 1), -100, device = "cuda:0")
        # model.model.extra_ignored_labels = extra_ignored_labels
        internal_model = model
        while hasattr(internal_model, "model"):
            internal_model.max_seq_length = max_seq_length
            internal_model = internal_model.model
        internal_model.max_seq_length = max_seq_length
        # Save to modules as well
        for module in model.modules():
            module.max_seq_length = max_seq_length

        # Patch tokenizer to pad to the right
        internal_model = model
        while hasattr(internal_model, "model"):
            if hasattr(internal_model, "_saved_temp_tokenizer"):
                internal_model._saved_temp_tokenizer.padding_side = "right"
            internal_model = internal_model.model
        if hasattr(internal_model, "_saved_temp_tokenizer"):
            internal_model._saved_temp_tokenizer.padding_side = "right"

        # Clear deleted GPU items
        for _ in range(3):
            gc.collect()
            clean_gpu_cache()

        patch_peft_fast_inference(model)

        # Add for_inference and for_training
        model.for_training = functools.partial(FastLlamaModel.for_training, model)
        model.for_inference = functools.partial(FastLlamaModel.for_inference, model)
        m = model
        while hasattr(m, "model"):
            m.for_training = functools.partial(FastBaseModel.for_training, m)
            m.for_inference = functools.partial(FastBaseModel.for_inference, m)
            m = m.model
        return model