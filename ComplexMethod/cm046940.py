def get_peft_model(
        model,
        r = 16,
        target_modules = [
            "query",
            "key",
            "value",
            "dense",
        ],
        lora_alpha = 16,
        lora_dropout = 0.0,
        bias = "none",
        layers_to_transform = None,
        layers_pattern = None,
        use_gradient_checkpointing = False,  # Changed default: conflicts with torch.compile
        random_state = 3407,
        max_seq_length = 2048,
        use_rslora = False,
        modules_to_save = None,
        init_lora_weights = True,
        loftq_config = {},
        **kwargs,
    ):
        from sentence_transformers import SentenceTransformer
        from peft import LoraConfig, get_peft_model as peft_get_peft_model

        if "task_type" not in kwargs:
            kwargs["task_type"] = "FEATURE_EXTRACTION"
            print("Setting task_type to FEATURE_EXTRACTION")

        if isinstance(model, SentenceTransformer):
            # Check if this is a fast encoder model (uses torch.compile instead of Unsloth patching)
            is_fast_encoder = getattr(model, "_unsloth_fast_encoder", False)

            if is_fast_encoder:
                # Fast encoder path: Use native PEFT + torch.compile (6x speedup)
                transformer_module = model[0]
                inner_model = transformer_module.auto_model

                # Check if model is quantized (4-bit/8-bit)
                is_quantized = (
                    getattr(inner_model, "is_quantized", False)
                    or getattr(inner_model.config, "quantization_config", None)
                    is not None
                )

                # Track if gradient checkpointing was actually enabled
                gc_enabled = False

                # this is needed when from_pretrained was called without gradient
                # checkpointing but get_peft_model requests it
                if use_gradient_checkpointing and use_gradient_checkpointing != False:
                    import transformers
                    from packaging.version import Version

                    transformers4 = Version(transformers.__version__).major < 5
                    model_type = getattr(inner_model.config, "model_type", "").lower()

                    if model_type == "mpnet" and transformers4:
                        FastSentenceTransformer._patch_mpnet_v4()
                    elif model_type == "mpnet":
                        FastSentenceTransformer._patch_mpnet_v5()

                # Prepare for k-bit training if quantized
                if is_quantized:
                    from ._utils import prepare_model_for_kbit_training

                    _gc_for_kbit = (
                        use_gradient_checkpointing
                        if use_gradient_checkpointing
                        else False
                    )
                    try:
                        inner_model = prepare_model_for_kbit_training(
                            inner_model,
                            use_gradient_checkpointing = _gc_for_kbit,
                        )
                        print("Unsloth: Prepared quantized model for k-bit training")
                        gc_enabled = bool(_gc_for_kbit)
                    except ValueError as e:
                        if "does not support gradient checkpointing" in str(e):
                            # Model doesn't support gradient checkpointing, disable it
                            print(
                                f"Unsloth Warning: {inner_model.__class__.__name__} does not support gradient checkpointing. Skipping."
                            )
                            inner_model = prepare_model_for_kbit_training(
                                inner_model,
                                use_gradient_checkpointing = False,
                            )
                            print(
                                "Unsloth: Prepared quantized model for k-bit training (without gradient checkpointing)"
                            )
                        else:
                            raise

                # Enable gradient checkpointing if requested (only for non-quantized, since prepare_model handles it)
                elif use_gradient_checkpointing and use_gradient_checkpointing != False:
                    if hasattr(inner_model, "gradient_checkpointing_enable"):
                        try:
                            inner_model.gradient_checkpointing_enable()
                            print("Unsloth: Enabled gradient checkpointing")
                            gc_enabled = True
                        except ValueError as e:
                            if "does not support gradient checkpointing" in str(e):
                                print(
                                    f"Unsloth Warning: {inner_model.__class__.__name__} does not support gradient checkpointing. Skipping."
                                )

                # Create LoRA config
                lora_config = LoraConfig(
                    r = r,
                    lora_alpha = lora_alpha,
                    target_modules = target_modules,
                    lora_dropout = lora_dropout,
                    bias = bias,
                    task_type = kwargs.get("task_type", "FEATURE_EXTRACTION"),
                )

                # Apply PEFT directly (not through FastModel)
                peft_model = peft_get_peft_model(inner_model, lora_config)

                # Apply QAT if specified
                qat_scheme = kwargs.get("qat_scheme", None)
                if qat_scheme is not None:
                    from ._utils import _prepare_model_for_qat

                    peft_model = _prepare_model_for_qat(peft_model, qat_scheme)

                # Determine compile mode (only if not using gradient checkpointing)
                compile_mode = getattr(model, "_compile_mode", "default")
                # Re-enable torch.compile if gradient checkpointing was requested but couldn't be enabled
                if compile_mode is None and not gc_enabled:
                    compile_mode = "default"
                    print(
                        "Unsloth: Re-enabling torch.compile since gradient checkpointing is not supported"
                    )

                # Re-assign the peft model back to the transformer module
                transformer_module.auto_model = peft_model

                # Store compile info for auto-compile at trainer time
                # torch.compile is deferred until training starts so we can check max_steps
                if compile_mode is not None:
                    model._compile_mode = compile_mode
                    model._compile_threshold = (
                        FastSentenceTransformer._estimate_compile_threshold(model)
                    )
                    # Flag to indicate compile has not been applied yet
                    model._compile_pending = True
                    print(
                        f"Unsloth: torch.compile will be applied automatically if max_steps > {model._compile_threshold}"
                    )
                else:
                    model._compile_mode = None
                    model._compile_pending = False
                    print(
                        "Unsloth: torch.compile disabled (gradient checkpointing enabled)"
                    )

                return model

            # Original path for non-fast-encoder models
            transformer_module = model[0]
            inner_model = transformer_module.auto_model

            peft_model = FastModel.get_peft_model(
                model = inner_model,
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
                **kwargs,
            )

            # re-assign the peft model back to the transformer module
            transformer_module.auto_model = peft_model
            return model
        else:
            return FastModel.get_peft_model(
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
                **kwargs,
            )