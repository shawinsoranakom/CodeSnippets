def from_pretrained(
        model_name = "unsloth/Llama-3.2-1B-Instruct",
        max_seq_length = 2048,
        dtype = None,
        load_in_4bit = True,  # 4bit QLoRA
        load_in_8bit = False,  # 8bit  LoRA
        load_in_16bit = False,  # 16bit LoRA
        full_finetuning = False,
        token = None,
        device_map = "sequential",
        rope_scaling = None,
        fix_tokenizer = True,
        trust_remote_code = False,
        use_gradient_checkpointing = "unsloth",
        resize_model_vocab = None,
        revision = None,
        use_exact_model_name = False,
        offload_embedding = False,
        float32_mixed_precision = None,  # Forces float32 mixed precision
        fast_inference = False,  # uses vLLM
        gpu_memory_utilization = 0.5,
        float8_kv_cache = False,
        random_state = 3407,
        max_lora_rank = 64,
        disable_log_stats = True,
        qat_scheme = None,
        load_in_fp8 = False,  # fp8 LoRA (True, False, 'block')
        unsloth_tiled_mlp = False,
        *args,
        **kwargs,
    ):
        # Respect user-provided quantization_config (e.g. BitsAndBytesConfig)
        quantization_config = kwargs.get("quantization_config", None)
        if quantization_config is not None:
            if isinstance(quantization_config, dict):
                q_load_in_4bit = quantization_config.get("load_in_4bit", False)
                q_load_in_8bit = quantization_config.get("load_in_8bit", False)
            else:
                q_load_in_4bit = getattr(quantization_config, "load_in_4bit", False)
                q_load_in_8bit = getattr(quantization_config, "load_in_8bit", False)
            if q_load_in_4bit:
                load_in_4bit = True
                load_in_8bit = False
            if q_load_in_8bit:
                load_in_8bit = True
                load_in_4bit = False

        # Login to allow private models
        token = hf_login(token)
        # Align dtype with bnb_4bit_compute_dtype if provided and dtype is unset.
        if dtype is None and quantization_config is not None:
            bnb_compute_dtype = None
            if isinstance(quantization_config, dict):
                if quantization_config.get("load_in_4bit", False):
                    bnb_compute_dtype = quantization_config.get(
                        "bnb_4bit_compute_dtype", None
                    )
            else:
                if getattr(quantization_config, "load_in_4bit", False):
                    bnb_compute_dtype = getattr(
                        quantization_config, "bnb_4bit_compute_dtype", None
                    )
            if isinstance(bnb_compute_dtype, str):
                bnb_compute_dtype = getattr(torch, bnb_compute_dtype, None)
            if isinstance(bnb_compute_dtype, torch.dtype):
                dtype = bnb_compute_dtype

        # Distributed-safe device placement for quantized models.
        # In multi-GPU (torchrun), each rank must load the model on its own device
        # to avoid Accelerate device relocation errors with quantized weights.
        is_quantized = load_in_4bit or load_in_8bit or load_in_fp8
        if is_quantized and isinstance(device_map, str):
            distributed_device_map, is_dist = prepare_device_map()
            if is_dist:
                device_map = distributed_device_map

        if load_in_8bit or full_finetuning or qat_scheme is not None:
            return FastModel.from_pretrained(
                model_name = model_name,
                max_seq_length = max_seq_length,
                dtype = dtype,
                load_in_4bit = load_in_4bit,
                load_in_8bit = load_in_8bit,
                load_in_16bit = load_in_16bit,
                full_finetuning = full_finetuning,
                token = token,
                device_map = device_map,
                rope_scaling = rope_scaling,  # [TODO] No effect
                fix_tokenizer = fix_tokenizer,  # [TODO] No effect
                trust_remote_code = trust_remote_code,
                use_gradient_checkpointing = use_gradient_checkpointing,
                resize_model_vocab = resize_model_vocab,  # [TODO] No effect
                revision = revision,
                return_logits = False,  # Return logits
                fullgraph = True,  # No graph breaks
                use_exact_model_name = use_exact_model_name,
                offload_embedding = offload_embedding,
                float32_mixed_precision = float32_mixed_precision,
                # Pass vLLM/inference parameters
                fast_inference = fast_inference,
                gpu_memory_utilization = gpu_memory_utilization,
                float8_kv_cache = float8_kv_cache,
                random_state = random_state,
                max_lora_rank = max_lora_rank,
                disable_log_stats = disable_log_stats,
                qat_scheme = qat_scheme,
                load_in_fp8 = load_in_fp8,
                unsloth_tiled_mlp = unsloth_tiled_mlp,
                *args,
                **kwargs,
            )

        if isinstance(dtype, str) and dtype in ["float16", "bfloat16"]:
            dtype = getattr(torch, dtype)
        assert (
            dtype is None
            or dtype == torch.float16
            or dtype == torch.bfloat16
            or dtype == torch.float32
        )

        if fast_inference:
            if importlib.util.find_spec("vllm") is None:
                raise ImportError(
                    "Unsloth: Please install vLLM before enabling `fast_inference`!\n"
                    "You can do this in a terminal via `pip install vllm`"
                )
            if DEVICE_TYPE_TORCH == "cuda":
                for i in range(DEVICE_COUNT):
                    # [TODO] DGX Spark vLLM breaks
                    if "NVIDIA GB10" in str(torch.cuda.get_device_name(i)).upper():
                        print(
                            "Unsloth: DGX Spark detected - `fast_inference=True` is currently broken as of January 2026.\n"
                            "Defaulting to native Unsloth inference."
                        )
                        fast_inference = False
                        break

        # Check if 4bit is allowed specifically for AMD
        if not ALLOW_BITSANDBYTES and not use_exact_model_name:
            if load_in_4bit or load_in_8bit or model_name.lower().endswith("-bnb-4bit"):
                print(
                    "Unsloth: AMD currently is not stable with 4bit bitsandbytes. Disabling for now."
                )
            load_in_4bit = False

        # Find FP8, BnB 4bit, other mapped names
        old_model_name = model_name
        fp8_mode = None
        if not use_exact_model_name:
            new_model_name = get_model_name(
                model_name,
                load_in_4bit = load_in_4bit,
                load_in_fp8 = load_in_fp8,
                token = token,
                trust_remote_code = trust_remote_code,
            )
            if new_model_name is None and load_in_fp8 != False:
                fp8_mode = _get_fp8_mode_and_check_settings(
                    load_in_fp8,
                    fast_inference,
                    full_finetuning,
                    load_in_4bit,
                    load_in_8bit,
                    load_in_16bit,
                )
                model_name = _offline_quantize_to_fp8(model_name, fp8_mode)
            else:
                assert new_model_name is not None
                model_name = new_model_name
                # If mapper resolved to a pre-quantized FP8 model, disable
                # on-the-fly quantization to avoid double quantization
                if load_in_fp8 != False and new_model_name != old_model_name:
                    load_in_fp8 = False

        # Check if pre-quantized models are allowed
        # AMD Instinct GPUs need blocksize = 128 on bitsandbytes < 0.49.2 (our pre-quants use blocksize = 64)
        if not ALLOW_PREQUANTIZED_MODELS and model_name.lower().endswith(
            ("-unsloth-bnb-4bit", "-bnb-4bit")
        ):
            model_name = _strip_unsloth_bnb_4bit_suffix(model_name)
        # Change -BF16 to all False for 4bit, 8bit etc
        if model_name.lower().endswith("-bf16"):
            load_in_4bit = False
            load_in_8bit = False
            load_in_fp8 = False
            load_in_16bit = True

        if USE_MODELSCOPE and not os.path.exists(model_name):
            from modelscope import snapshot_download

            model_name = snapshot_download(model_name)

        # First check if it's a normal model via AutoConfig
        from huggingface_hub.utils import (
            disable_progress_bars,
            enable_progress_bars,
            are_progress_bars_disabled,
        )

        was_disabled = are_progress_bars_disabled()
        disable_progress_bars()

        autoconfig_error = None
        peft_error = None
        model_config = None
        peft_config = None
        local_files_only = kwargs.get("local_files_only", False)

        try:
            model_config = AutoConfig.from_pretrained(
                model_name,
                token = token,
                revision = revision,
                trust_remote_code = trust_remote_code,
                local_files_only = local_files_only,
            )
            is_model = True
        except ImportError:
            raise
        except Exception as error:
            autoconfig_error = str(error)
            if "architecture" in autoconfig_error:
                if "qwen3_5" in autoconfig_error:
                    raise ImportError(
                        f"Unsloth: Your transformers version of {transformers_version} does not support Qwen3.5.\n"
                        f"The minimum required version is 5.2.0.\n"
                        f'Try `pip install --upgrade "transformers>=5.2.0"`\n'
                        f"to obtain the latest transformers build, then restart this session."
                    )
                raise ValueError(
                    f"`{model_name}` is not supported yet in `transformers=={transformers_version}`.\n"
                    f"Please update transformers via `pip install --upgrade transformers` and try again."
                )
            is_model = False
        try:
            peft_config = PeftConfig.from_pretrained(
                model_name,
                token = token,
                revision = revision,
                trust_remote_code = trust_remote_code,
                local_files_only = local_files_only,
            )
            is_peft = True
        except ImportError:
            raise
        except Exception as error:
            peft_error = str(error)
            if "architecture" in peft_error:
                raise ValueError(
                    f"`{model_name}` is not supported yet in `transformers=={transformers_version}`.\n"
                    f"Please update transformers via `pip install --upgrade transformers` and try again."
                )
            is_peft = False

        # Old transformers versions check
        both_exist = (is_model and is_peft) and not SUPPORTS_LLAMA32

        # Error out if both LoRA and normal model config exists.
        if both_exist:
            raise RuntimeError(
                "Unsloth: Your repo has a LoRA adapter and a base model.\n"
                "You have 2 files `config.json` and `adapter_config.json`.\n"
                "We must only allow one config file.\n"
                "Please separate the LoRA and base models to 2 repos."
            )
        model_types = get_transformers_model_type(
            peft_config if peft_config is not None else model_config,
            trust_remote_code = trust_remote_code,
        )
        if len(model_types) == 1:
            model_type = model_types[0]
        else:
            # Leave as tuple if more than one arch
            model_type = model_types

        # New transformers need to check manually.
        if SUPPORTS_LLAMA32 and is_model and is_peft:
            # Check if folder exists locally
            if os.path.isdir(model_name):
                exist_adapter_config = os.path.exists(
                    os.path.join(model_name, "adapter_config.json")
                )
                exist_config = os.path.exists(os.path.join(model_name, "config.json"))
                both_exist = exist_adapter_config and exist_config
            else:
                # Both AutoConfig and PeftConfig loaded successfully from this
                # remote repo, so both config.json and adapter_config.json
                # definitely exist -- no need for an extra HfFileSystem network call.
                both_exist = True

        if not is_model and not is_peft:
            error = autoconfig_error if autoconfig_error is not None else peft_error
            # Old transformers version
            if "rope_scaling" in error.lower() and not SUPPORTS_LLAMA31:
                raise ImportError(
                    f"Unsloth: Your transformers version of {transformers_version} does not support new RoPE scaling methods.\n"
                    f"This includes Llama 3.1. The minimum required version is 4.43.2\n"
                    f'Try `pip install --upgrade "transformers>=4.43.2"`\n'
                    f"to obtain the latest transformers build, then restart this session."
                )
            # Create a combined error message showing both failures
            combined_error = (
                "Unsloth: Failed to load model. Both AutoConfig and PeftConfig loading failed.\n\n"
                f"AutoConfig error: {autoconfig_error}\n\n"
                f"PeftConfig error: {peft_error}\n\n"
            )
            raise RuntimeError(combined_error)

        # Get base model for PEFT:
        if is_peft:
            # Check base model again for PEFT
            model_name = peft_config.base_model_name_or_path
            if not use_exact_model_name:
                model_name = get_model_name(
                    model_name,
                    load_in_4bit = load_in_4bit,
                    load_in_fp8 = load_in_fp8,
                    token = token,
                    trust_remote_code = trust_remote_code,
                )
            # Check if pre-quantized models are allowed
            # AMD Instinct GPUs need blocksize = 128 on bitsandbytes < 0.49.2 (our pre-quants use blocksize = 64)
            if not ALLOW_PREQUANTIZED_MODELS and model_name.lower().endswith(
                ("-unsloth-bnb-4bit", "-bnb-4bit")
            ):
                model_name = _strip_unsloth_bnb_4bit_suffix(model_name)
            # Change -BF16 to all False for 4bit, 8bit etc
            if model_name.lower().endswith("-bf16"):
                load_in_4bit = False
                load_in_8bit = False
                load_in_fp8 = False
                load_in_16bit = True

            model_config = AutoConfig.from_pretrained(
                model_name,
                token = token,
                trust_remote_code = trust_remote_code,
                local_files_only = local_files_only,
            )

        if not was_disabled:
            enable_progress_bars()

        if model_type == "llama":
            scaling_type = None
            if getattr(model_config, "rope_scaling", None) is not None:
                scaling_type1 = model_config.rope_scaling.get("type", None)
                scaling_type2 = model_config.rope_scaling.get("rope_type", None)
                scaling_type = (
                    scaling_type1 if scaling_type1 is not None else scaling_type2
                )

            if scaling_type == "llama3" and not SUPPORTS_LLAMA31:
                raise ImportError(
                    f"Unsloth: Your transformers version of {transformers_version} does not support Llama 3.1.\n"
                    f"The minimum required version is 4.43.2\n"
                    f'Try `pip install --upgrade "transformers>=4.43.2"`\n'
                    f"to obtain the latest transformers build, then restart this session."
                )

            dispatch_model = FastLlamaModel

        elif model_type == "mistral":
            dispatch_model = FastMistralModel
        elif model_type == "gemma":
            if not SUPPORTS_GEMMA:
                raise ImportError(
                    f"Unsloth: Your transformers version of {transformers_version} does not support Gemma.\n"
                    f"The minimum required version is 4.38.\n"
                    f'Try `pip install --upgrade "transformers>=4.38"`\n'
                    f"to obtain the latest transformers build, then restart this session."
                )
            dispatch_model = FastGemmaModel
        elif model_type == "gemma2":
            if not SUPPORTS_GEMMA2:
                raise ImportError(
                    f"Unsloth: Your transformers version of {transformers_version} does not support Gemma2.\n"
                    f"The minimum required version is 4.42.3.\n"
                    f'Try `pip install --upgrade "transformers>=4.42.3"`\n'
                    f"to obtain the latest transformers build, then restart this session."
                )
            # Also check for softcapping support in flash-attn which is faster!
            if is_bfloat16_supported() and not HAS_FLASH_ATTENTION:
                print(
                    "Unsloth: If you want to finetune Gemma 2, install flash-attn to make it faster!\n"
                    "To install flash-attn, do the below:\n"
                    '\npip install --no-deps --upgrade "flash-attn>=2.6.3"'
                )
            elif HAS_FLASH_ATTENTION and not HAS_FLASH_ATTENTION_SOFTCAPPING:
                print(
                    "Unsloth: If you want to finetune Gemma 2, upgrade flash-attn to version 2.6.3 or higher!\n"
                    "Newer versions support faster and less memory usage kernels for Gemma 2's attention softcapping!\n"
                    "To update flash-attn, do the below:\n"
                    '\npip install --no-deps --upgrade "flash-attn>=2.6.3"'
                )

            dispatch_model = FastGemma2Model
        elif model_type == "qwen2":
            dispatch_model = FastQwen2Model
        elif model_type == "qwen3":  # or model_type == "qwen3_moe":
            if not SUPPORTS_QWEN3 or not SUPPORTS_QWEN3_MOE:
                raise ImportError(
                    f"Unsloth: Your transformers version of {transformers_version} does not support Qwen3.\n"
                    f"The minimum required version is 4.50.3.\n"
                    f'Try `pip install --upgrade "transformers>=4.50.3"`\n'
                    f"to obtain the latest transformers build, then restart this session."
                )
            dispatch_model = (
                FastQwen3Model if model_type == "qwen3" else FastQwen3MoeModel
            )
        # elif model_type == "falcon_h1":
        #     dispatch_model = FastFalconH1Model
        #     if not SUPPORTS_FALCON_H1:
        #         raise ImportError(
        #             f"Unsloth: Your transformers version of {transformers_version} does not support FalconH1.\n"\
        #             f"The minimum required version is 4.50.3.\n"\
        #             f'Try `pip install --upgrade "transformers>=4.50.3"`\n'\
        #             f"to obtain the latest transformers build, then restart this session."\
        #         )
        # Temporary disable optimized Cohere until errors match
        # elif model_type == "cohere":
        #     dispatch_model = FastCohereModel
        # Temporary disable optimized Granite until errors match
        # elif model_type == "granite":
        #     dispatch_model = FastGraniteModel
        else:
            return FastModel.from_pretrained(
                model_name = old_model_name,
                max_seq_length = max_seq_length,
                dtype = dtype,
                load_in_4bit = load_in_4bit,
                load_in_8bit = load_in_8bit,
                load_in_16bit = load_in_16bit,
                full_finetuning = full_finetuning,
                token = token,
                device_map = device_map,
                rope_scaling = rope_scaling,  # [TODO] No effect
                fix_tokenizer = fix_tokenizer,  # [TODO] No effect
                trust_remote_code = trust_remote_code,
                use_gradient_checkpointing = use_gradient_checkpointing,
                resize_model_vocab = resize_model_vocab,  # [TODO] No effect
                revision = revision,
                return_logits = False,  # Return logits
                fullgraph = True,  # No graph breaks
                use_exact_model_name = use_exact_model_name,
                offload_embedding = offload_embedding,
                float32_mixed_precision = float32_mixed_precision,
                # Pass vLLM/inference parameters
                fast_inference = fast_inference,
                gpu_memory_utilization = gpu_memory_utilization,
                float8_kv_cache = float8_kv_cache,
                random_state = random_state,
                max_lora_rank = max_lora_rank,
                disable_log_stats = disable_log_stats,
                qat_scheme = qat_scheme,
                load_in_fp8 = load_in_fp8,
                unsloth_tiled_mlp = unsloth_tiled_mlp,
                *args,
                **kwargs,
            )

        # Apply gradient checkpointing with smart heuristics
        use_gradient_checkpointing = apply_unsloth_gradient_checkpointing(
            use_gradient_checkpointing, max_seq_length, dtype
        )

        # Check if this is local model since the tokenizer gets overwritten
        if (
            os.path.exists(os.path.join(old_model_name, "tokenizer_config.json"))
            and os.path.exists(os.path.join(old_model_name, "tokenizer.json"))
            and os.path.exists(os.path.join(old_model_name, "special_tokens_map.json"))
        ):
            tokenizer_name = old_model_name
        else:
            tokenizer_name = kwargs.pop("tokenizer_name", None)

        if fast_inference:
            fast_inference, model_name = fast_inference_setup(model_name, model_config)

        load_in_4bit_kwargs = load_in_4bit
        load_in_8bit_kwargs = load_in_8bit
        if quantization_config is not None and not fast_inference:
            load_in_4bit_kwargs = False
            load_in_8bit_kwargs = False

        model, tokenizer = dispatch_model.from_pretrained(
            model_name = model_name,
            max_seq_length = max_seq_length,
            dtype = _get_dtype(dtype),
            load_in_4bit = load_in_4bit_kwargs,
            token = token,
            device_map = device_map,
            rope_scaling = rope_scaling,
            fix_tokenizer = fix_tokenizer,
            model_patcher = dispatch_model,
            tokenizer_name = tokenizer_name,
            trust_remote_code = trust_remote_code,
            revision = revision if not is_peft else None,
            fast_inference = fast_inference,
            gpu_memory_utilization = gpu_memory_utilization,
            float8_kv_cache = float8_kv_cache,
            random_state = random_state,
            max_lora_rank = max_lora_rank,
            disable_log_stats = disable_log_stats,
            load_in_fp8 = load_in_fp8,
            *args,
            **kwargs,
        )

        if resize_model_vocab is not None:
            model.resize_token_embeddings(resize_model_vocab)

        # In case the model supports tagging, add the unsloth tag.
        if hasattr(model, "add_model_tags"):
            model.add_model_tags(
                [
                    "unsloth",
                ]
            )
        if hasattr(tokenizer, "add_model_tags"):
            tokenizer.add_model_tags(
                [
                    "unsloth",
                ]
            )

        if load_in_4bit:
            # Fix up bitsandbytes config, but respect user-provided quantization_config
            if quantization_config is None:
                compute_dtype = dtype_from_config(model.config)
                quantization_config = {
                    # Sometimes compute_dtype is not a string!!
                    "bnb_4bit_compute_dtype": compute_dtype,
                    "bnb_4bit_quant_type": "nf4",
                    "bnb_4bit_use_double_quant": True,
                    "llm_int8_enable_fp32_cpu_offload": False,
                    "llm_int8_has_fp16_weight": False,
                    "llm_int8_skip_modules": None,
                    "llm_int8_threshold": 6.0,
                    "load_in_4bit": True,
                    "load_in_8bit": False,
                    "quant_method": "bitsandbytes",
                }
                model.config.update({"quantization_config": quantization_config})
            else:
                if hasattr(quantization_config, "to_dict"):
                    model.config.update(
                        {"quantization_config": quantization_config.to_dict()}
                    )
                elif isinstance(quantization_config, dict):
                    model.config.update({"quantization_config": quantization_config})

        if load_in_fp8 != False:
            _tag_model_with_fp8_torchao_config(model, fp8_mode)

        if is_peft:
            # From https://github.com/huggingface/peft/issues/184
            # Now add PEFT adapters
            model = PeftModel.from_pretrained(
                model,
                old_model_name,
                token = token,
                revision = revision,
                is_trainable = True,
                trust_remote_code = trust_remote_code,
            )
            # Patch it as well!
            model = dispatch_model.patch_peft_model(model, use_gradient_checkpointing)

        # Patch Tiled MLP
        # to turn on set UNSLOTH_TILED_MLP to "arctic", "target", or "target:{GB}""
        patch_tiled_mlp_choice = os.environ.get(
            "UNSLOTH_TILED_MLP", "arctic" if unsloth_tiled_mlp else "0"
        )
        if patch_tiled_mlp_choice != "0" or unsloth_tiled_mlp:
            patch_tiled_mlp(model, patch_options_str = patch_tiled_mlp_choice)

        model = _fix_rope_inv_freq(model)
        return model, tokenizer