def get_peft_model(
        model,
        r = 16,
        target_modules = [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_alpha = 16,
        lora_dropout = 0.0,
        bias = "none",
        layers_to_transform = None,
        layers_pattern = None,
        use_gradient_checkpointing = "unsloth",
        random_state = 3407,
        max_seq_length = 2048,  # not used anymore
        use_rslora = False,
        modules_to_save = None,
        init_lora_weights = True,
        loftq_config = {},
        temporary_location = "_unsloth_temporary_saved_buffers",
        qat_scheme = None,
        target_parameters = None,  # For MoE expert layers (nn.Parameter)
        ensure_weight_tying = False,
        **kwargs,
    ):
        if os.environ.get("UNSLOTH_USE_NEW_MODEL", "0") == "1":
            # Check for other PEFT args in kwargs
            for peft_arg, flag in (
                ("finetune_vision_layers", False),
                ("finetune_language_layers", True),
                ("finetune_attention_modules", True),
                ("finetune_mlp_modules", True),
            ):
                if peft_arg not in kwargs:
                    kwargs[peft_arg] = flag
            return FastBaseModel.get_peft_model(
                model = model,
                r = r,
                target_modules = target_modules,
                lora_alpha = lora_alpha,
                lora_dropout = lora_dropout,
                bias = bias,
                layers_to_transform = layers_to_transform,
                layers_pattern = layers_pattern,
                use_gradient_checkpointing = use_gradient_checkpointing,
                random_state = random_state,
                max_seq_length = max_seq_length,
                use_rslora = use_rslora,
                modules_to_save = modules_to_save,
                init_lora_weights = init_lora_weights,
                loftq_config = loftq_config,
                temporary_location = temporary_location,
                target_parameters = target_parameters,
                ensure_weight_tying = ensure_weight_tying,
                **kwargs,
            )
        if os.environ.get("UNSLOTH_ENABLE_FULL_FINETUNING", "0") == "1":
            print(
                "Unsloth: Full finetuning is enabled, so .get_peft_model has no effect"
            )
            return model
        transformers_set_seed(random_state)

        # Apply gradient checkpointing with smart heuristics
        max_seq = getattr(model, "max_seq_length", 512)
        dtype = model.get_input_embeddings().weight.dtype
        use_gradient_checkpointing = apply_unsloth_gradient_checkpointing(
            use_gradient_checkpointing, max_seq, dtype
        )

        if type(r) is not int:
            raise TypeError(f"Unsloth: Rank of {str(r)} must be an integer.")
        if r <= 0:
            raise TypeError(f"Unsloth: Rank of {str(r)} must be larger than 0.")

        if isinstance(model, PeftModelForCausalLM) or isinstance(
            model, PeftModelForSequenceClassification
        ):
            # Check if exactly the same and then pass through!
            assert hasattr(model, "peft_config")

            peft_config = model.peft_config["default"].to_dict()
            check_parameters = [
                "r",
                "lora_alpha",
                "lora_dropout",
                "bias",
                "layers_to_transform",
                "layers_pattern",
                "use_rslora",
                "init_lora_weights",
            ]
            check_all = True
            for param in check_parameters:
                check_all = check_all and (peft_config[param] == eval(param))

            # Check save_modules
            old_target_modules = list(peft_config["target_modules"])
            modules_to_save = peft_config["modules_to_save"]
            if modules_to_save is None:
                modules_to_save = {}
            modules_to_save = list(modules_to_save)
            old_target_modules += modules_to_save

            # Combine all
            new_target_modules = list(target_modules) + list(
                modules_to_save if modules_to_save is not None else []
            )

            # Now check!
            new_target_modules = set(new_target_modules)
            check_all = check_all and (
                len(set(old_target_modules) ^ new_target_modules) == 0
            )

            check_all = check_all and (
                (loftq_config == {} or loftq_config is None)
                and (
                    peft_config["loftq_config"] == {}
                    or peft_config["loftq_config"] is None
                )
            )

            if check_all:
                # Simply pass through!
                logger.warning(
                    "Unsloth: Already have LoRA adapters! We shall skip this step."
                )

                # Offload!
                # [TODO] First offload lm_head and embed_tokens to CPU (should be disk!!)
                if "embed_tokens" in new_target_modules:
                    print(
                        "Unsloth: Training embed_tokens in mixed precision to save VRAM"
                    )

                    _offload_frozen_module_for_training(
                        model.get_input_embeddings(), DEVICE_TYPE_TORCH
                    )

                if "lm_head" in new_target_modules:
                    print("Unsloth: Training lm_head in mixed precision to save VRAM")

                    _offload_frozen_module_for_training(
                        model.get_output_embeddings(), DEVICE_TYPE_TORCH
                    )

                return model
            else:
                raise TypeError(
                    "Unsloth: Your model already has LoRA adapters. Your new parameters are different."
                )

        if loftq_config is None:
            loftq_config = {}

        signature = str(inspect.signature(LoraConfig))
        SUPPORTS_LOFTQ = "loftq_config" in signature
        SUPPORTS_RSLORA = "use_rslora" in signature

        if lora_dropout != 0:
            logger.warning_once(
                f"Unsloth: Dropout = 0 is supported for fast patching. You are using dropout = {lora_dropout}.\n"
                f"Unsloth will patch all other layers, except LoRA matrices, causing a performance hit."
            )

        if bias != "none":
            logger.warning_once(
                f"Unsloth: bias = `none` is supported for fast patching. You are using bias = {bias}.\n"
                f"Unsloth will patch all other layers, except LoRA matrices, causing a performance hit."
            )

        if not (
            type(init_lora_weights) is bool
            or init_lora_weights == "gaussian"
            or init_lora_weights == "loftq"
            or init_lora_weights == "corda"
        ):
            raise ValueError(
                'Unsloth: `init_lora_weights` must be either [True, False, "gaussian", "loftq", "corda"].'
            )

        if init_lora_weights == "loftq":
            if not SUPPORTS_LOFTQ:
                import peft

                raise RuntimeError(
                    f"Unsloth: Your PEFT version of {peft.__version__} does not support LoftQ init.\n"
                    "Please install PEFT 0.7.2 or higher.\n"
                    "You can also install from source: `pip install git+https://github.com/huggingface/peft.git"
                )

            if loftq_config == {}:
                from peft import LoftQConfig

                logger.warning_once(
                    "Unsloth: init_lora_weights = `loftq` is set, but `loftq_config` is None.\n"
                    "We shall use `loftq_config = LoftQConfig(loftq_bits = 4, loftq_iter = 1)`."
                )
                loftq_config = LoftQConfig(loftq_bits = 4, loftq_iter = 1)

            if hasattr(model.config, "quantization_config"):
                raise ValueError(
                    "Unsloth: You are using `loftq` init, yet `load_in_4bit = True` was set.\n"
                    "Reload your model without any quantization by setting `load_in_4bit = False`."
                )

        assert type(use_rslora) is bool
        if use_rslora:
            if not SUPPORTS_RSLORA:
                # We manually check for PEFT
                import peft

                raise RuntimeError(
                    f"Unsloth: Your PEFT version of {peft.__version__} does not support `use_rslora`.\n"
                    "Please install PEFT 0.7.2 or higher.\n"
                    "You can also install from source: `pip install git+https://github.com/huggingface/peft.git"
                )

        accepted_modules = frozenset(
            (
                "lm_head",
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ),
        )
        model.config.update({"unsloth_version": __version__})

        if type(modules_to_save) is tuple:
            modules_to_save = list(modules_to_save)

        train_lm_head = False
        train_embed_tokens = False
        final_modules = []
        for module in target_modules:
            if module == "embed_tokens":
                # logger.warning_once(
                #     "Unsloth: `embed_tokens` should be placed in `modules_to_save` and not `target_modules`. "\
                #     "Luckily, we shall do it for you!"
                # )
                train_embed_tokens = True
                if modules_to_save is None:
                    modules_to_save = ["embed_tokens"]
                else:
                    modules_to_save.append("embed_tokens")

            else:
                try:
                    assert module in accepted_modules
                    final_modules.append(module)
                except AssertionError as e:
                    final_modules.append(module)
                    print(
                        "Unsloth: You added custom modules, but Unsloth hasn't optimized for this.\n"
                        "Beware - your finetuning might be noticeably slower!"
                    )
                pass

        # Check if we added new tokens!
        if hasattr(model, "_need_to_train_embeddings"):
            # Check if embed_tokens/lm_head are already being trained
            # (either as LoRA targets in final_modules or via modules_to_save)
            _embed_already_trained = (
                train_embed_tokens or "embed_tokens" in final_modules
            )
            _lm_head_already_trained = train_lm_head or "lm_head" in final_modules
            if not _lm_head_already_trained or not _embed_already_trained:
                print(
                    "Unsloth: You added new tokens but did not specify if you wanted to "
                    "train the lm_head and embed_tokens.\nWe must turn it on for you."
                )

                # Only add to modules_to_save if not already a LoRA target
                if not _embed_already_trained:
                    train_embed_tokens = True
                    if modules_to_save is None:
                        modules_to_save = ["embed_tokens"]
                    elif "embed_tokens" not in modules_to_save:
                        modules_to_save.append("embed_tokens")

                if not _lm_head_already_trained:
                    train_lm_head = True
                    if modules_to_save is None:
                        modules_to_save = ["lm_head"]
                    elif "lm_head" not in modules_to_save:
                        modules_to_save.append("lm_head")

        # Check for Llama-3
        # if hasattr(model._saved_temp_tokenizer, "_using_llama3_template"):
        #     if not train_embed_tokens and not train_lm_head:
        #         raise RuntimeError("")

        # First fix untrained tokens
        # Wrong - can cause reserved tokens to pop out!!
        # if train_embed_tokens or train_lm_head:
        #     fix_untrained_tokens(model, eps = 1e-16)
        # pass

        # Check modules_to_save
        if modules_to_save is not None:
            for module in modules_to_save:
                if module == "lm_head":
                    train_lm_head = True
                elif module == "embed_tokens":
                    train_embed_tokens = True
                else:
                    raise TypeError(
                        f"Unsloth: Module = {module} is not allowed. Only 'lm_head' and 'embed_tokens' is allowed."
                    )
        if isinstance(modules_to_save, (tuple, list)):
            modules_to_save = list(set(modules_to_save))

        vllm_engine = None
        if hasattr(model, "vllm_engine"):
            # Fast inference!
            vllm_engine = model.vllm_engine
            vllm_fast_generate = model.fast_generate
            vllm_fast_generate_batches = model.fast_generate_batches

            if modules_to_save is not None:
                raise NotImplementedError(
                    "Unsloth: Currently fast inference does not work with training embeddings or lm_head."
                )

            if bias != "none":
                raise NotImplementedError(
                    "Unsloth: Currently fast inference does not work with using biases for LoRA."
                )

        # Does not get lora yet, so get name from model, not base model
        is_classification = "Classification" in str(type(model))

        # Auto-detect MoE models and populate target_parameters for expert layers
        if target_parameters is None:
            target_parameters = get_moe_target_parameters(model, target_modules)

        arguments = dict(
            r = r,
            lora_alpha = lora_alpha,
            target_modules = final_modules,
            lora_dropout = lora_dropout,
            bias = bias,
            task_type = TaskType.CAUSAL_LM if not is_classification else TaskType.SEQ_CLS,
            layers_to_transform = layers_to_transform,
            init_lora_weights = init_lora_weights,
            loftq_config = loftq_config,
            use_rslora = use_rslora,
            modules_to_save = modules_to_save,
            target_parameters = target_parameters,
            ensure_weight_tying = ensure_weight_tying,
            **kwargs,
        )
        if not SUPPORTS_LOFTQ:
            del arguments["loftq_config"]
        if not SUPPORTS_RSLORA:
            del arguments["use_rslora"]

        _saved_temp_tokenizer = model._saved_temp_tokenizer

        lora_config = LoraConfig(**arguments)
        # First offload lm_head and embed_tokens to disk
        input_embeddings_device = model.get_input_embeddings().weight.device
        if is_classification:
            output_embeddings_device = model.score.weight.device
        else:
            output_embeddings_device = model.get_output_embeddings().weight.device

        if use_gradient_checkpointing == "unsloth":
            if train_embed_tokens:
                print("Unsloth: Offloading input_embeddings to disk to save VRAM")
                offload_input_embeddings(model, temporary_location)

            # Remove old items to save VRAM
            for _ in range(3):
                gc.collect()
                clean_gpu_cache()

            if train_lm_head:
                print("Unsloth: Offloading output_embeddings to disk to save VRAM")
                offload_output_embeddings(model, temporary_location)

            # Remove old items to save VRAM
            for _ in range(3):
                gc.collect()
                clean_gpu_cache()

        model = _get_peft_model(model, lora_config)
        # Fix LoraConfig.auto_mapping is None
        fix_lora_auto_mapping(model)

        # Apply QAT + LoRA if specified
        if qat_scheme is not None:
            print("Unsloth: Applying QAT to mitigate quantization degradation")
            model = FastLlamaModel._prepare_for_qat(model, qat_scheme)

        model._saved_temp_tokenizer = _saved_temp_tokenizer

        model = FastLlamaModel.patch_peft_model(model, use_gradient_checkpointing)

        if ensure_weight_tying:
            try:
                input_embeddings = model.get_input_embeddings()
                output_embeddings = model.get_output_embeddings()

                if input_embeddings is not None and output_embeddings is not None:

                    def _retie_parameter(target_module, source_module):
                        if not hasattr(source_module, "weight"):
                            return
                        weight = source_module.weight
                        # Remove existing registration to avoid "attribute already exists"
                        if "weight" in getattr(target_module, "_parameters", {}):
                            target_module._parameters.pop("weight")
                        if hasattr(target_module, "weight"):
                            try:
                                delattr(target_module, "weight")
                            except Exception as exc:
                                logger.warning_once(
                                    f"Unsloth: Could not delete existing weight attr during retie on "
                                    f"{type(target_module).__name__}: {exc}"
                                )
                        target_module.register_parameter("weight", weight)

                    # Tie trainable copies created by ModulesToSaveWrapper first (these are used in forward)
                    if hasattr(input_embeddings, "modules_to_save") and hasattr(
                        output_embeddings, "modules_to_save"
                    ):
                        if hasattr(
                            input_embeddings.modules_to_save, "default"
                        ) and hasattr(output_embeddings.modules_to_save, "default"):
                            _retie_parameter(
                                output_embeddings.modules_to_save.default,
                                input_embeddings.modules_to_save.default,
                            )

                    # Tie original_module references as well if present
                    if hasattr(input_embeddings, "original_module") and hasattr(
                        output_embeddings, "original_module"
                    ):
                        _retie_parameter(
                            output_embeddings.original_module,
                            input_embeddings.original_module,
                        )
            except Exception as e:
                logger.warning_once(
                    f"Unsloth: Failed to ensure weight tying between embeddings and lm_head: {e}"
                )

        if train_embed_tokens:
            print("Unsloth: Training embed_tokens in mixed precision to save VRAM")
            assert hasattr(model.get_input_embeddings(), "modules_to_save")

            _offload_frozen_module_for_training(
                model.get_input_embeddings(), DEVICE_TYPE_TORCH, offload_device = None
            )

        if train_lm_head:
            print("Unsloth: Training lm_head in mixed precision to save VRAM")
            assert hasattr(model.get_output_embeddings(), "modules_to_save")

            _offload_frozen_module_for_training(
                model.get_output_embeddings(), DEVICE_TYPE_TORCH, offload_device = None
            )

        # Patch tokenizer to pad to the right
        internal_model = model
        while hasattr(internal_model, "model"):
            if hasattr(internal_model, "_saved_temp_tokenizer"):
                internal_model._saved_temp_tokenizer.padding_side = "right"
            # Also set is_loaded_in_8bit to disable incorrect DDP
            internal_model.is_loaded_in_8bit = True
            internal_model = internal_model.model
        if hasattr(internal_model, "_saved_temp_tokenizer"):
            internal_model._saved_temp_tokenizer.padding_side = "right"
        # Also set is_loaded_in_8bit to disable incorrect DDP
        internal_model.is_loaded_in_8bit = True

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