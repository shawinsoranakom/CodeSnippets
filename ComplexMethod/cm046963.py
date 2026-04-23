def from_pretrained(
        model_name = "unsloth/Llama-3.2-1B-Instruct",
        max_seq_length = 2048,
        dtype = None,
        load_in_4bit = True,
        load_in_8bit = False,
        load_in_16bit = False,
        full_finetuning = False,
        token = None,
        device_map = "sequential",
        trust_remote_code = False,
        model_types = None,
        tokenizer_name = None,
        auto_model = AutoModelForVision2Seq,
        use_gradient_checkpointing = "unsloth",
        supports_sdpa = True,
        whisper_language = None,
        whisper_task = None,
        auto_config = None,
        offload_embedding = False,
        float32_mixed_precision = None,  # Forces float32 mixed precision
        # vLLM parameters
        fast_inference = False,
        gpu_memory_utilization = 0.5,
        float8_kv_cache = False,
        random_state = 3407,
        max_lora_rank = 64,
        disable_log_stats = False,
        unsloth_vllm_standby = False,
        load_in_fp8 = False,  # fp8 LoRA (True, False, 'block')
        **kwargs,
    ):
        if unsloth_vllm_standby and os.environ.get("UNSLOTH_VLLM_STANDBY", "0") != "1":
            raise RuntimeError(
                "Unsloth: UNSLOTH_VLLM_STANDBY is True, but UNSLOTH_VLLM_STANDBY is not set to 1!"
            )

        if model_types is None:
            raise RuntimeError(
                "Unsloth: Please use FastModel or FastVisionModel and not use FastBaseModel directly!"
            )
        if os.environ.get("UNSLOTH_MODEL_NAME", "") == "":
            os.environ["UNSLOTH_MODEL_NAME"] = model_name.lower()

        is_vlm = auto_model in [AutoModelForVision2Seq, AutoModelForImageTextToText]
        is_whisper = whisper_language is not None and whisper_task is not None
        auto_processor = AutoProcessor if (is_vlm or is_whisper) else AutoTokenizer

        model_type_arch = model_types[0]
        if model_type_arch == "siglip":
            for model_type_arch in model_types:
                if model_type_arch != "siglip":
                    break

        vllm_enable_lora = True

        if is_vlm and fast_inference:
            if not any(arch in VLLM_SUPPORTED_VLM for arch in model_types):
                raise RuntimeError(
                    f"Unsloth: Fast inference is only supported for Language models and Qwen2.5-VL, Gemma3 among vision models. "
                    f"Found architectures: {', '.join(model_types)}!"
                )

        if any(arch in VLLM_NON_LORA_VLM for arch in model_types):
            # mllama is still only in vllm v0 https://arc.net/l/quote/llwkfgmu
            # https://docs.vllm.ai/en/stable/models/supported_models.html#text-generation_1
            # vLLM V0 does not support LoRA on multi modal models.
            # TODO: Update this once vLLM V1 supports Llama 3.2 aka mllama
            vllm_enable_lora = False

        os.environ["UNSLOTH_USE_NEW_MODEL"] = "1"
        if trust_remote_code:
            print(
                "Unsloth: WARNING `trust_remote_code` is True.\n"
                "Are you certain you want to do remote code execution?"
            )
        token = hf_login(token)
        SUPPORTS_BFLOAT16 = is_bfloat16_supported()

        if DEVICE_TYPE == "cuda":
            gpu_stats = torch.cuda.get_device_properties(0)
            gpu_stats_name = (
                gpu_stats.name + ". " if gpu_stats.name != "" else "NVIDIA GPU Device. "
            )
            gpu_version = torch.version.cuda
            gpu_stats_snippet = f"CUDA: {gpu_stats.major}.{gpu_stats.minor}. CUDA Toolkit: {gpu_version}."
            try:
                vllm_version = f" vLLM: {importlib_version('vllm')}."
            except:
                vllm_version = ""
        elif DEVICE_TYPE == "hip":
            gpu_stats = torch.cuda.get_device_properties(0)
            gpu_stats_name = resolve_hip_gpu_stats_name(gpu_stats)
            gpu_version = torch.version.hip
            gpu_stats_snippet = f"ROCm Toolkit: {gpu_version}."
            try:
                vllm_version = f" vLLM: {importlib_version('vllm')}."
            except:
                vllm_version = ""
        elif DEVICE_TYPE == "xpu":
            gpu_stats = torch.xpu.get_device_properties(0)
            gpu_stats_name = (
                gpu_stats.name + ". " if gpu_stats.name != "" else "Intel XPU Device. "
            )
            gpu_version = torch.version.xpu
            gpu_stats_snippet = f"Intel Toolkit: {gpu_version}."
            # [TODO] After adding vLLM support for XPU, change this
            vllm_version = ""
        else:
            raise ValueError(f"Unsloth: Unsupported device type: {DEVICE_TYPE}")

        max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)

        arch_name = model_type_arch.title()
        arch_name = arch_name.replace("_Vl_", "_VL_").replace("_Moe", "_MoE")
        statistics = (
            f"==((====))==  Unsloth {__version__}: Fast {arch_name} patching. Transformers: {transformers_version}.{vllm_version}\n"
            f"   {chr(92)}{chr(92)}   /|    {gpu_stats_name}Num GPUs = {DEVICE_COUNT}. Max memory: {max_memory} GB. Platform: {platform_system}.\n"
            f"O^O/ {chr(92)}_/ {chr(92)}    Torch: {torch.__version__}. {gpu_stats_snippet} Triton: {triton_version}\n"
            f"{chr(92)}        /    Bfloat16 = {str(SUPPORTS_BFLOAT16).upper()}. FA [Xformers = {xformers_version}. FA2 = {HAS_FLASH_ATTENTION}]\n"
            f' "-____-"     Free license: http://github.com/unslothai/unsloth'
        )

        print(statistics)

        # Warn about fast transfers
        if "HF_HUB_ENABLE_HF_TRANSFER" in os.environ:
            old_hf_transfer = os.environ["HF_HUB_ENABLE_HF_TRANSFER"]
            if old_hf_transfer in ("False", "false"):
                old_hf_transfer = "0"
            if old_hf_transfer in ("True", "true"):
                old_hf_transfer = "1"
        else:
            old_hf_transfer = "0"
        if old_hf_transfer == "1":
            print(
                "Unsloth: Fast downloading is enabled - ignore downloading bars which are red colored!"
            )
        if old_hf_transfer != "0":
            os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

        # For debugging - we use a download counter to see if environments are not breaking or if HF is down
        get_statistics(kwargs.get("local_files_only", False))

        if dtype is None:
            dtype = torch.float16 if not SUPPORTS_BFLOAT16 else torch.bfloat16
        elif os.environ.get("UNSLOTH_FORCE_FLOAT32", "0") == "1":
            if dtype == torch.float16:
                dtype = torch.bfloat16
        elif dtype == torch.bfloat16 and not SUPPORTS_BFLOAT16:
            logger.warning_once(
                "Device does not support bfloat16. Will change to float16."
            )
            dtype = torch.float16
        assert dtype in (torch.float16, torch.bfloat16, torch.float32)

        bnb_compute_dtype = dtype
        do_forced_float32 = False
        if os.environ.get("UNSLOTH_FORCE_FLOAT32", "0") == "1":
            print(
                f"Unsloth: Using float16 precision for {model_type_arch} won't work! Using float32."
            )
            bnb_compute_dtype = torch.float16
            do_forced_float32 = True

        # Check for custom data-types
        custom_datatype = None
        correct_dtype = None
        if os.environ.get("UNSLOTH_FORCE_CUSTOM_DTYPE", "") != "":
            custom_datatype = os.environ["UNSLOTH_FORCE_CUSTOM_DTYPE"]
            assert custom_datatype.count(";") >= 4
            checker, _dtype, _bnb_compute_dtype, _custom_datatype, execute_code = (
                custom_datatype.split(";", 4)
            )
            # Allow custom dtypes on all runs
            allow_all_runs = checker == "all"
            # Allow only on float16 datatypes
            allow_float16_runs = (
                checker == "float16" or checker == "torch.float16"
            ) and (
                dtype == torch.float16
                or os.environ.get("UNSLOTH_FORCE_FLOAT32", "0") == "1"
            )
            if allow_all_runs or allow_float16_runs:
                if eval(_dtype) is not None:
                    dtype = eval(_dtype)
                if eval(_bnb_compute_dtype) is not None:
                    bnb_compute_dtype = eval(_bnb_compute_dtype)
                correct_dtype = bnb_compute_dtype
                custom_datatype = _custom_datatype
                # Execute code as well
                if len(execute_code.strip()) != 0:
                    exec(execute_code)
            else:
                custom_datatype = None
                correct_dtype = None

        if auto_config is None:
            auto_config = AutoConfig.from_pretrained(
                model_name,
                token = token,
                trust_remote_code = trust_remote_code,
            )
        model_class = resolve_model_class(auto_model, auto_config)
        attn_impl = resolve_attention_implementation(
            model_class,
            auto_config,
            requested_attn_implementation = kwargs.get("attn_implementation", None),
            supports_sdpa = supports_sdpa,
        )

        # Handle FP8 models: get_model_name has already redirected this to BF16 sibling if the model ships with
        # FP8 weights. We just need to update it here for sanity.
        auto_config.model_name = model_name
        kwargs["attn_implementation"] = attn_impl

        bnb_config = None
        user_quantization_config = kwargs.get("quantization_config", None)
        if full_finetuning and (load_in_4bit or load_in_8bit):
            print(
                "Unsloth: You selected full finetuning support, but 4bit / 8bit is enabled - disabling LoRA / QLoRA."
            )
            load_in_4bit = False
            load_in_8bit = False
            load_in_16bit = False

        if int(load_in_4bit) + int(load_in_8bit) + int(load_in_16bit) >= 2:
            raise RuntimeError(
                "Unsloth: Can only load in 4bit or 8bit or 16bit, not a combination!"
            )
        _skip_modules = SKIP_QUANTIZATION_MODULES.copy()
        # Nemotron-H uses 'mixer' (not 'mamba') for Mamba layers.
        # Mamba fused kernels pass out_proj.weight directly to F.linear,
        # which fails with quantized Params4bit. Skip out_proj from quantization.
        if any(mt == "nemotron_h" for mt in (model_types or [])):
            _skip_modules.append("out_proj")

        if load_in_4bit:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit = True,
                bnb_4bit_use_double_quant = True,
                bnb_4bit_quant_type = "nf4",
                bnb_4bit_compute_dtype = bnb_compute_dtype,
                llm_int8_skip_modules = _skip_modules,
            )
        elif load_in_8bit:
            bnb_config = BitsAndBytesConfig(
                load_in_8bit = True,
                llm_int8_skip_modules = _skip_modules,
            )
        elif load_in_16bit:
            bnb_config = None
        elif not load_in_4bit and not load_in_8bit and not full_finetuning:
            print(
                "Unsloth: QLoRA and full finetuning all not selected. Switching to 16bit LoRA."
            )

        if full_finetuning:
            os.environ["UNSLOTH_ENABLE_FULL_FINETUNING"] = "1"
            if dtype == torch.bfloat16:
                if float32_mixed_precision != True:
                    print(
                        f"Unsloth: Using bfloat16 full finetuning which cuts memory usage by 50%.\n"
                        f"To enable float32 training, use `float32_mixed_precision = True` during FastLanguageModel.from_pretrained"
                    )
                else:
                    print(
                        f"Unsloth: Using full float32 full finetuning. "
                        f"To enable bfloat16 training to reduce VRAM usage by 50% albeit with a slightly higher loss, do:\n"
                        "use `float32_mixed_precision = False` during FastLanguageModel.from_pretrained"
                    )
                    os.environ["UNSLOTH_BFLOAT16_MIXED_PRECISION"] = "1"
            else:
                print(
                    "Unsloth: Float16 full finetuning uses more memory since we upcast weights to float32."
                )
        else:
            os.environ["UNSLOTH_ENABLE_FULL_FINETUNING"] = "0"

        # Fix AttributeError: 'BitsAndBytesConfig' object has no attribute 'get_loading_attributes'
        if bnb_config is not None and not hasattr(bnb_config, "get_loading_attributes"):
            bnb_config.get_loading_attributes = lambda *args, **kwargs: {}

        # Cannot be None, since HF now checks for the config
        if load_in_4bit or load_in_8bit:
            # Ignore load_in_4bit / load_in_8bit for MXFP4 - best to get config file
            if (
                "gpt-oss-20b" in model_name.lower()
                or "gpt-oss-120b" in model_name.lower()
            ):
                pass
            else:
                if user_quantization_config is None:
                    kwargs["quantization_config"] = bnb_config
        else:
            if auto_config is None:
                auto_config = AutoConfig.from_pretrained(
                    model_name,
                    token = token,
                    trust_remote_code = trust_remote_code,
                )
            if hasattr(auto_config, "quantization_config"):
                from transformers.quantizers.auto import (
                    AUTO_QUANTIZATION_CONFIG_MAPPING,
                )

                quantization_config = auto_config.quantization_config
                quant_method = quantization_config["quant_method"]
                # Sometimes bitsandbytes_4bit + bitsandbytes_8bit is provided
                if (
                    quant_method == "bitsandbytes"
                    and "bitsandbytes" not in AUTO_QUANTIZATION_CONFIG_MAPPING
                ):
                    if "bitsandbytes_4bit" not in AUTO_QUANTIZATION_CONFIG_MAPPING:
                        raise KeyError(
                            "Unsloth: AUTO_QUANTIZATION_CONFIG_MAPPING does not have `bitsandbytes_4bit`"
                        )
                    quantizer = AUTO_QUANTIZATION_CONFIG_MAPPING["bitsandbytes_4bit"]
                else:
                    quantizer = AUTO_QUANTIZATION_CONFIG_MAPPING[quant_method]
                quantizer_kwargs = {}
                if quant_method == "compressed-tensors":
                    # Ignore these
                    pass
                else:
                    # We cannot dequantize since gpt-oss-20b MXFP4 will now be gpt-oss-20b-BF16
                    if (
                        load_in_16bit
                        and "dequantize" in inspect.signature(quantizer).parameters
                    ):
                        quantizer_kwargs["dequantize"] = True
                    try:
                        # Sometimes this fails so we wrap it in a try except
                        quantization_config = quantizer.from_dict(
                            quantization_config, **quantizer_kwargs
                        )
                    except:
                        pass
                    if user_quantization_config is None:
                        kwargs["quantization_config"] = quantization_config

        # Check if using forced float32 - we load it in bfloat16, then cast to float16!
        torch_dtype = dtype
        if do_forced_float32:
            torch_dtype = torch.bfloat16

        kwargs = add_dtype_kwargs(torch_dtype, kwargs)

        config_attn_impl = kwargs.get("attn_implementation", None)
        if config_attn_impl is None:
            config_attn_impl = "sdpa" if supports_sdpa else "eager"
        if auto_config is None:
            auto_config = AutoConfig.from_pretrained(
                model_name,
                token = token,
                trust_remote_code = trust_remote_code,
            )
        _set_attn_impl(auto_config, config_attn_impl)
        model_config = auto_config

        verify_fp8_support_if_applicable(model_config)

        raise_handler = RaiseUninitialized()
        if not fast_inference:
            # Prevent load_in_fp8 from being forwarded into HF internal model loading
            load_in_fp8 = kwargs.pop("load_in_fp8", None)
            # Transformers 5.x @strict config classes reject unexpected kwargs.
            # Move config-level attributes onto the config object directly.
            _num_labels = kwargs.pop("num_labels", None)
            if _num_labels is not None:
                model_config.num_labels = _num_labels
            for _cfg_key in ("id2label", "label2id", "max_position_embeddings"):
                _cfg_val = kwargs.pop(_cfg_key, None)
                if _cfg_val is not None:
                    setattr(model_config, _cfg_key, _cfg_val)
            model = auto_model.from_pretrained(
                model_name,
                config = model_config,
                device_map = device_map,
                # torch_dtype           = torch_dtype, # Transformers removed torch_dtype
                # quantization_config   = bnb_config,
                token = token,
                trust_remote_code = trust_remote_code,
                # attn_implementation   = attn_implementation,
                **kwargs,
            )
            # Attach dispatch hooks for bnb multi-device loads.
            _attach_bnb_multidevice_hooks(
                model,
                load_in_4bit = load_in_4bit,
                load_in_8bit = load_in_8bit,
                offload_embedding = offload_embedding,
                fast_inference = fast_inference,
            )
            if hasattr(model, "generate"):
                model.fast_generate = make_fast_generate_wrapper(model.generate)
                model.fast_generate_batches = error_out_no_vllm
            if offload_embedding:
                if bool(
                    os.environ.get("WSL_DISTRO_NAME") or os.environ.get("WSL_INTEROP")
                ):
                    # WSL doesn't work with offloaded embeddings
                    pass
                elif os.name == "nt":
                    # Windows doesn't work with offloaded embeddings
                    pass
                else:
                    embed_tokens = model.get_input_embeddings()
                    nbytes = embed_tokens.weight.numel() * embed_tokens.weight.itemsize
                    ngb = round(nbytes / 1024 / 1024 / 1024, 2)
                    print(f"Unsloth: Offloading embeddings to RAM to save {ngb} GB.")
                    embed_tokens.to("cpu")

                    # Add hooks to move inputs to CPU and back to CUDA
                    # [TODO] Doesn't seem to work!
                    # def pre_hook(module, args):
                    #     args[0]._old_device = args[0].device
                    #     return (args[0].to("cpu", non_blocking = True))
                    # def post_hook(module, args, output):
                    #     old_device = getattr(args[0], "_old_device", "cuda")
                    #     return output.to(old_device, non_blocking = True)
                    # embed_tokens.register_forward_pre_hook(pre_hook,  prepend = True)
                    # embed_tokens.register_forward_hook    (post_hook, prepend = True)
                    # Must free GPU memory otherwise will not free!
                    torch.cuda.empty_cache()
                    gc.collect()
        else:
            from unsloth_zoo.vllm_utils import (
                load_vllm,
                get_vllm_state_dict,
                convert_vllm_to_huggingface,
                generate_batches,
                get_lora_supported_ranks,
            )

            if full_finetuning:
                max_lora_rank = max(get_lora_supported_ranks())
                raise NotImplementedError(
                    "Unsloth: `fast_inference=True` cannot be used together with `full_finetuning=True`.\n"
                    "Reason: fast_inference is optimized for inference-only workflows and "
                    "does not currently support full fine-tuning.\n"
                    "Workaround: disable fast_inference, or use parameter-efficient fine-tuning "
                    f"(e.g. LoRA with rank r={max_lora_rank})."
                )

            model_config.model_name = model_name

            if fast_inference:
                fast_inference, model_name = fast_inference_setup(
                    model_name, model_config
                )

            fp8_mode = None
            if load_in_fp8 != False:
                fp8_mode = _get_fp8_mode_and_check_settings(
                    load_in_fp8,
                    fast_inference,
                    full_finetuning,
                    load_in_4bit,
                    load_in_8bit,
                    load_in_16bit,
                )

            allowed_args = inspect.getfullargspec(load_vllm).args
            load_vllm_kwargs = dict(
                model_name = model_name,
                config = model_config,
                gpu_memory_utilization = gpu_memory_utilization,
                max_seq_length = max_seq_length,
                dtype = dtype,
                float8_kv_cache = float8_kv_cache,
                enable_lora = vllm_enable_lora,
                max_lora_rank = max_lora_rank,
                disable_log_stats = disable_log_stats,
                use_bitsandbytes = load_in_4bit,
                unsloth_vllm_standby = unsloth_vllm_standby,
                is_vision_model = is_vlm,
                fp8_mode = fp8_mode,
            )
            for allowed_arg in allowed_args:
                if allowed_arg not in load_vllm_kwargs and allowed_arg in kwargs:
                    load_vllm_kwargs[allowed_arg] = kwargs[allowed_arg]

            # Load vLLM first
            llm = load_vllm(**load_vllm_kwargs)

            # Convert to HF format
            _, quant_state_dict = get_vllm_state_dict(
                llm,
                config = model_config,
                is_vision_model = is_vlm,
                load_in_fp8 = load_in_fp8,
            )
            model = convert_vllm_to_huggingface(
                quant_state_dict,
                model_config,
                dtype,
                bnb_config,
                is_vision_model = is_vlm,
            )
            model.vllm_engine = llm
            model.fast_generate = model.vllm_engine.generate
            model.fast_generate_batches = functools.partial(
                generate_batches, model.vllm_engine
            )

        raise_handler.remove()

        # Return old flag
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = old_hf_transfer

        # Check float32 norm weights
        if os.environ.get("UNSLOTH_HIGH_PRECISION_LAYERNORM", "0") == "1":
            for jj, (name, module) in enumerate(model.named_modules()):
                if (
                    name.endswith(("norm", "norm1", "norm2", "norm3", "norm4"))
                    or "layernorm" in name
                    or "layer_norm" in name
                ) and hasattr(module, "weight"):
                    module._pre_set_compute_dtype = torch.float32
        # Edit data-types
        if custom_datatype is not None:
            with torch.no_grad():
                for jj, (name, module) in enumerate(model.named_modules()):
                    exec(custom_datatype)
        # Clear deleted GPU items
        for _ in range(3):
            gc.collect()
            if DEVICE_TYPE in ("cuda", "hip"):
                torch.cuda.empty_cache()
            elif DEVICE_TYPE == "xpu":
                torch.xpu.empty_cache()

        # Counteract saved tokenizers
        tokenizer_name = model_name if tokenizer_name is None else tokenizer_name

        # Fix _Unsloth_Patched_ prefix in local config files from old saves (issue #4085)
        if os.path.isdir(tokenizer_name):
            import json as _json

            for _cfg_name in (
                "processor_config.json",
                "preprocessor_config.json",
                "tokenizer_config.json",
            ):
                _cfg_path = os.path.join(tokenizer_name, _cfg_name)
                if os.path.exists(_cfg_path):
                    try:
                        with open(_cfg_path, "r", encoding = "utf-8") as _f:
                            _cfg = _json.load(_f)
                        if _cfg.get("processor_class", "").startswith(
                            "_Unsloth_Patched_"
                        ):
                            _cfg["processor_class"] = _cfg["processor_class"][
                                len("_Unsloth_Patched_") :
                            ]
                            with open(_cfg_path, "w", encoding = "utf-8") as _f:
                                _json.dump(_cfg, _f, indent = 2, ensure_ascii = False)
                    except Exception:
                        pass

        if (whisper_language and whisper_task) or auto_model.__name__.endswith(
            "ForConditionalGeneration"
        ):
            try:
                tokenizer = auto_processor.from_pretrained(
                    tokenizer_name,
                    padding_side = "left",
                    token = token,
                    language = whisper_language,
                    task = whisper_task,
                    trust_remote_code = trust_remote_code,
                )
            except Exception:
                tokenizer = None
        else:
            try:
                tokenizer = auto_processor.from_pretrained(
                    tokenizer_name,
                    padding_side = "left",
                    token = token,
                    trust_remote_code = trust_remote_code,
                )
            except:
                tokenizer = get_auto_processor(
                    tokenizer_name,
                    padding_side = "left",
                    token = token,
                    trust_remote_code = trust_remote_code,
                )

        # If processor loading failed (e.g., tokenizer class not found),
        # or if AutoProcessor silently degraded to a text-only tokenizer
        # instead of returning a full VLM processor (issue #4085),
        # try constructing the processor manually from separate components.
        _processor_is_degraded = (
            is_vlm
            and tokenizer is not None
            and not hasattr(tokenizer, "image_processor")
        )
        if (tokenizer is None or _processor_is_degraded) and is_vlm:
            _fallback = _construct_vlm_processor_fallback(
                tokenizer_name,
                model_type_arch,
                token,
                trust_remote_code,
            )
            if _fallback is not None:
                tokenizer = _fallback
            if tokenizer is None:
                import sys

                print(
                    f"Unsloth: Warning - VLM processor fallback returned None for model_type={model_type_arch}",
                    file = sys.stderr,
                )
        # Backwards compat: if processor has no chat_template (e.g. old saves without
        # chat_template.jinja) but the inner tokenizer does, copy it to the processor.
        if (
            hasattr(tokenizer, "tokenizer")
            and getattr(tokenizer, "chat_template", None) is None
            and getattr(tokenizer.tokenizer, "chat_template", None) is not None
        ):
            tokenizer.chat_template = tokenizer.tokenizer.chat_template

        if hasattr(tokenizer, "tokenizer"):
            __tokenizer = tokenizer.tokenizer
            # Add padding side as well
            __tokenizer.padding_side = "left"
            # Check bos, eos, pad tokens
            if hasattr(__tokenizer, "bos_token"):
                tokenizer.bos_token = __tokenizer.bos_token
                tokenizer.bos_token_id = __tokenizer.bos_token_id
            if hasattr(__tokenizer, "eos_token"):
                tokenizer.eos_token = __tokenizer.eos_token
                tokenizer.eos_token_id = __tokenizer.eos_token_id
            if hasattr(__tokenizer, "pad_token"):
                tokenizer.pad_token = __tokenizer.pad_token
                tokenizer.pad_token_id = __tokenizer.pad_token_id
        # Fix other stuff like BnB compute data types
        model, tokenizer = patch_model_and_tokenizer(
            model,
            tokenizer,
            downcast_rope = False,
            fix_embeddings = False,
            do_forced_float32 = do_forced_float32,
            correct_dtype = correct_dtype,
        )

        try:
            model, tokenizer = patch_tokenizer(model, tokenizer)
        except Exception as _patch_err:
            # Some VLM processors (e.g., ERNIE VL) may fail during tokenizer patching.
            # Try loading tokenizer separately via AutoTokenizer as fallback.
            try:
                from transformers import AutoTokenizer as _AutoTokenizer

                _fallback_tok = _AutoTokenizer.from_pretrained(
                    tokenizer_name,
                    padding_side = "left",
                    token = token,
                    trust_remote_code = trust_remote_code,
                )
                model, _fallback_tok = patch_tokenizer(model, _fallback_tok)
                # Re-attach as processor wrapper if original was a processor
                if hasattr(tokenizer, "image_processor"):
                    tokenizer.tokenizer = _fallback_tok
                else:
                    tokenizer = _fallback_tok
            except Exception:
                # If fallback also fails, raise the original error
                raise _patch_err
        model = post_patch_loss_function(model)

        # Log Unsloth version for future fastpaths for inference
        if hasattr(model, "config"):
            model.config.update({"unsloth_version": __version__})
        patch_saving_functions(model, vision = True)
        if tokenizer is None:
            # Last resort: try loading tokenizer via AutoTokenizer, then PreTrainedTokenizerFast
            try:
                from transformers import AutoTokenizer as _AutoTokenizer

                tokenizer = _AutoTokenizer.from_pretrained(
                    tokenizer_name,
                    padding_side = "left",
                    token = token,
                    trust_remote_code = trust_remote_code,
                )
            except Exception:
                try:
                    from transformers import PreTrainedTokenizerFast

                    tokenizer = PreTrainedTokenizerFast.from_pretrained(
                        tokenizer_name,
                        padding_side = "left",
                        token = token,
                        trust_remote_code = trust_remote_code,
                    )
                except Exception:
                    del model
                    raise RuntimeError(
                        "Unsloth: The tokenizer is weirdly not loaded? Please check if there is one."
                    )
        patch_saving_functions(tokenizer, vision = True)

        # Fix gradient accumulation. See issue #4982.
        from transformers.trainer import Trainer

        apply_accepts_loss_kwargs_fix(model)
        patch_gradient_accumulation_fix(Trainer)

        # Save tokenizer for inference purposes
        tokenizer.padding_side = "left"  # Force inference
        if hasattr(tokenizer, "tokenizer"):
            tokenizer.tokenizer.padding_side = "left"  # Force inference
        m = model
        while hasattr(m, "model"):
            m.max_seq_length = max_seq_length
            m._saved_temp_tokenizer = tokenizer
            # Also set is_loaded_in_8bit to disable incorrect DDP
            m.is_loaded_in_8bit = True if not full_finetuning else False
            m = m.model
        m.max_seq_length = max_seq_length
        # Save to modules as well
        for module in model.modules():
            module.max_seq_length = max_seq_length
        m._saved_temp_tokenizer = tokenizer
        # Also set is_loaded_in_8bit to disable incorrect DDP
        m.is_loaded_in_8bit = True if not full_finetuning else False

        # Patch generate
        if os.environ.get("UNSLOTH_DISABLE_FAST_GENERATION", "0") == "0" and hasattr(
            model, "generate"
        ):
            if model.generate.__name__ != "unsloth_base_fast_generate":
                model._old_generate = model.generate
                unsloth_base_fast_generate.__doc__ = model._old_generate.__doc__
                model.generate = types.MethodType(unsloth_base_fast_generate, model)
        model._unsloth_trust_remote_code = trust_remote_code
        # Post patches
        model = FastBaseModel.post_patch_model(
            model,
            use_gradient_checkpointing = use_gradient_checkpointing,
            trust_remote_code = trust_remote_code,
            model_type = model_type_arch,
            tokenizer = tokenizer,
            float32_mixed_precision = float32_mixed_precision,
        )
        # Clear deleted GPU items
        for _ in range(3):
            gc.collect()
            if DEVICE_TYPE in ("cuda", "hip"):
                torch.cuda.empty_cache()
            elif DEVICE_TYPE == "xpu":
                torch.xpu.empty_cache()
        return model, tokenizer