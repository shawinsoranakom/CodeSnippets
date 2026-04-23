def from_pretrained(
        model_name = "unsloth/llama-3-8b-bnb-4bit",
        max_seq_length = None,
        dtype = None,
        load_in_4bit = True,
        token = None,
        device_map = "sequential",
        rope_scaling = None,
        fix_tokenizer = True,
        model_patcher = None,
        tokenizer_name = None,
        trust_remote_code = False,
        revision = None,
        fast_inference = False,  # uses vLLM
        gpu_memory_utilization = 0.5,
        float8_kv_cache = False,
        random_state = 3407,
        max_lora_rank = 16,
        disable_log_stats = False,
        unsloth_vllm_standby = False,
        num_labels = None,
        qat_scheme = None,
        load_in_fp8 = False,  # fp8 LoRA (True, False, 'block')
        **kwargs,
    ):
        os.environ["UNSLOTH_USE_NEW_MODEL"] = "0"
        if trust_remote_code:
            if fast_inference:
                raise NotImplementedError(
                    "Unsloth: Fast inference does not support `trust_remote_code` yet."
                )
            print(
                "Unsloth: WARNING `trust_remote_code` is True.\n"
                "Are you certain you want to do remote code execution?"
            )
        if fast_inference:
            if not is_vLLM_available():
                print("Unsloth: vLLM is not installed! Will use Unsloth inference!")
                fast_inference = False
            if DEVICE_TYPE == "cuda":
                major_version, minor_version = torch.cuda.get_device_capability()
                if major_version < 7:
                    print(
                        "Unsloth: vLLM does not work on older GPUs - will switch to Unsloth inference!"
                    )
                    fast_inference = False
            elif DEVICE_TYPE == "hip":
                fast_inference = True
            if (
                unsloth_vllm_standby
                and os.environ.get("UNSLOTH_VLLM_STANDBY", "0") == "0"
            ):
                raise RuntimeError(
                    "Unsloth: `unsloth_vllm_standby` is True, but  environment variable `UNSLOTH_VLLM_STANDBY` is not set to 1!"
                )

        token = hf_login(token)
        if model_patcher is None:
            model_patcher = FastLlamaModel
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
            try:
                vllm_version = f" vLLM: {importlib_version('vllm')}."
            except:
                vllm_version = ""
        else:
            raise ValueError(f"Unsloth: Unsupported device type: {DEVICE_TYPE}")

        max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)

        statistics = (
            f"==((====))==  Unsloth {__version__}: Fast {model_patcher.__name__[4:-5]} patching. Transformers: {transformers_version}.{vllm_version}\n"
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

        model_patcher.pre_patch()
        # For debugging - we use a download counter to see if environments are not breaking or if HF is down
        get_statistics(kwargs.get("local_files_only", False))

        if dtype is None:
            dtype = torch.float16 if not SUPPORTS_BFLOAT16 else torch.bfloat16
        elif dtype == torch.bfloat16 and not SUPPORTS_BFLOAT16:
            logger.warning_once(
                "Device does not support bfloat16. Will change to float16."
            )
            dtype = torch.float16
        # elif dtype == torch.float16 and SUPPORTS_BFLOAT16:
        #     logger.warning_once("Device supports bfloat16 but you selected float16. Will change to bfloat16.")
        #     dtype = torch.bfloat16

        assert (
            dtype == torch.float16 or dtype == torch.bfloat16 or dtype == torch.float32
        )

        # RoPE Scaling
        model_config = AutoConfig.from_pretrained(
            model_name,
            token = token,
            attn_implementation = "sdpa",
        )
        model_config.model_name = model_name
        model_max_seq_length = model_config.max_position_embeddings

        verify_fp8_support_if_applicable(model_config)

        # Check if RoPE Scaling is even allowed
        model_function = MODEL_FOR_CAUSAL_LM_MAPPING[model_config.__class__]
        IS_FALCON_H1 = model_config.model_type.startswith("falcon_h1")

        preferred_attn_impl = resolve_attention_implementation(
            model_function, model_config
        )

        has_rope_scaling = False
        try:
            with open(inspect.getfile(model_function), "r", encoding = "utf-8") as file:
                has_rope_scaling = "self.config.rope_scaling" in file.read()
        except:
            pass
        has_rope_scaling = True

        # If max_seq_length is not specified, use maximum from config
        if max_seq_length is None:
            max_seq_length = model_max_seq_length

        if (rope_scaling is None) and (max_seq_length > model_max_seq_length):
            rope_scaling = max_seq_length / model_max_seq_length

            if fast_inference:
                raise NotImplementedError(
                    "Unsloth: Fast inference does not yet work with RoPE Scaling."
                )

            logger.warning_once(
                f"Unsloth: {model_name} can only handle sequence lengths of at most "
                f"{model_max_seq_length}.\nBut with kaiokendev's RoPE scaling of "
                f"{round(rope_scaling, 3)}, it can be magically be extended to "
                f"{max_seq_length}!"
            )

            # Warn RoPE scaling isn't allowed
            if not has_rope_scaling:
                raise RuntimeError(
                    f"However, {model_name} doesn't support RoPE Scaling!\n"
                    "Please file a feature request at https://github.com/unslothai/unsloth."
                )

            rope_scaling = {
                "type": "linear",
                "factor": rope_scaling,
            }

            # Add to kwargs
            kwargs["rope_scaling"] = rope_scaling

        bnb_config = None
        if load_in_4bit:
            llm_int8_skip_modules = SKIP_QUANTIZATION_MODULES.copy()
            if IS_FALCON_H1:
                # we cannot quantize out_proj layer due to mamba kernels: https://github.com/tiiuae/Falcon-H1/issues/13#issuecomment-2918671274
                llm_int8_skip_modules.append("out_proj")
            bnb_config = BitsAndBytesConfig(
                load_in_4bit = True,
                bnb_4bit_use_double_quant = True,
                bnb_4bit_quant_type = "nf4",
                bnb_4bit_compute_dtype = dtype,
                llm_int8_skip_modules = llm_int8_skip_modules,
            )
            # For pre-quantized checkpoints (e.g. unsloth/Qwen3-4B-bnb-4bit),
            # transformers uses the quantization_config baked into the
            # checkpoint's config.json and ignores the runtime BitsAndBytesConfig
            # we pass via kwargs. Merge our skip list into that bundled config
            # so task heads like `score` (for *ForSequenceClassification) stay
            # in the compute dtype. See unslothai/unsloth#5027.
            _ckpt_qcfg = getattr(model_config, "quantization_config", None)
            if _ckpt_qcfg is not None:
                if isinstance(_ckpt_qcfg, dict):
                    _ckpt_skip = list(_ckpt_qcfg.get("llm_int8_skip_modules") or [])
                    for _m in llm_int8_skip_modules:
                        if _m not in _ckpt_skip:
                            _ckpt_skip.append(_m)
                    _ckpt_qcfg["llm_int8_skip_modules"] = _ckpt_skip
                else:
                    _ckpt_skip = list(
                        getattr(_ckpt_qcfg, "llm_int8_skip_modules", None) or []
                    )
                    for _m in llm_int8_skip_modules:
                        if _m not in _ckpt_skip:
                            _ckpt_skip.append(_m)
                    try:
                        _ckpt_qcfg.llm_int8_skip_modules = _ckpt_skip
                    except Exception:
                        pass

        # https://huggingface.co/togethercomputer/LLaMA-2-7B-32K/discussions/12
        # RoPE Scaling's max_position_embeddings must be updated
        max_position_embeddings = max(max_seq_length, model_max_seq_length)
        kwargs.pop("attn_implementation", None)  # No need since we auto call it

        # Cannot be None, since HF now checks for the config
        if load_in_4bit:
            kwargs["quantization_config"] = bnb_config

        kwargs = add_dtype_kwargs(dtype, kwargs)

        raise_handler = RaiseUninitialized()
        if num_labels is not None:
            # Transformers 5.x @strict config classes reject unexpected kwargs
            # like num_labels and max_position_embeddings. Set on the config
            # object directly and pass config= instead.
            model_config.num_labels = num_labels
            if max_position_embeddings is not None:
                model_config.max_position_embeddings = max_position_embeddings
            # Pop config-level attrs that would be rejected by @strict model init
            for _cfg_key in ("id2label", "label2id", "rope_scaling"):
                _cfg_val = kwargs.pop(_cfg_key, None)
                if _cfg_val is not None:
                    setattr(model_config, _cfg_key, _cfg_val)
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                config = model_config,
                device_map = device_map,
                # torch_dtype             = dtype, # transformers changed torch_dtype to dtype
                # quantization_config     = bnb_config,
                token = token,
                trust_remote_code = trust_remote_code,
                attn_implementation = preferred_attn_impl,
                **kwargs,
            )
            # Defensive: make sure the task head ended up in a floating dtype.
            # The primary protection is SKIP_QUANTIZATION_MODULES plus the skip
            # list merge above; this guards against a downstream path accidentally
            # leaving the head in an integer storage. See unslothai/unsloth#5027.
            for _head_name in ("score", "classifier", "qa_outputs"):
                _head = getattr(model, _head_name, None)
                if (
                    _head is not None
                    and hasattr(_head, "weight")
                    and not _head.weight.is_floating_point()
                ):
                    _head.to(dtype)
            # Attach dispatch hooks for bnb multi-device loads.
            from unsloth.models.vision import _attach_bnb_multidevice_hooks

            _attach_bnb_multidevice_hooks(
                model,
                load_in_4bit = load_in_4bit,
                load_in_8bit = kwargs.get("load_in_8bit", False),
                offload_embedding = False,
                fast_inference = fast_inference,
            )
        elif not fast_inference:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map = device_map,
                # torch_dtype             = dtype, # transformers changed torch_dtype to dtype
                # quantization_config     = bnb_config,
                token = token,
                max_position_embeddings = max_position_embeddings,
                trust_remote_code = trust_remote_code,
                attn_implementation = preferred_attn_impl,
                **kwargs,
            )
            # Attach dispatch hooks for bnb multi-device loads.
            from unsloth.models.vision import _attach_bnb_multidevice_hooks

            _attach_bnb_multidevice_hooks(
                model,
                load_in_4bit = load_in_4bit,
                load_in_8bit = kwargs.get("load_in_8bit", False),
                offload_embedding = False,
                fast_inference = False,
            )
            model.fast_generate = make_fast_generate_wrapper(model.generate)
            model.fast_generate_batches = None
        else:
            from unsloth_zoo.vllm_utils import (
                load_vllm,
                get_vllm_state_dict,
                convert_vllm_to_huggingface,
                generate_batches,
            )

            fp8_mode = None
            if load_in_fp8 != False:
                fp8_mode = _get_fp8_mode_and_check_settings(
                    load_in_fp8,
                    fast_inference,
                )

            allowed_args = inspect.getfullargspec(load_vllm).args
            load_vllm_kwargs = dict(
                model_name = model_name,
                config = model_config,
                gpu_memory_utilization = gpu_memory_utilization,
                max_seq_length = max_seq_length,
                dtype = dtype,
                float8_kv_cache = float8_kv_cache,
                enable_lora = True,
                max_lora_rank = max_lora_rank,
                disable_log_stats = disable_log_stats,
                use_bitsandbytes = load_in_4bit,
                unsloth_vllm_standby = unsloth_vllm_standby,
                fp8_mode = fp8_mode,
            )
            for allowed_arg in allowed_args:
                if allowed_arg not in load_vllm_kwargs and allowed_arg in kwargs:
                    load_vllm_kwargs[allowed_arg] = kwargs[allowed_arg]
            pass

            # Load vLLM first
            llm = load_vllm(**load_vllm_kwargs)

            # Convert to HF format
            _, quant_state_dict = get_vllm_state_dict(
                llm,
                config = model_config,
                load_in_fp8 = load_in_fp8,
            )
            model = convert_vllm_to_huggingface(
                quant_state_dict, model_config, dtype, bnb_config
            )
            model.vllm_engine = llm
            model.fast_generate = model.vllm_engine.generate
            model.fast_generate_batches = functools.partial(
                generate_batches, model.vllm_engine
            )
        raise_handler.remove()
        # Return old flag
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = old_hf_transfer

        # Counteract saved tokenizers
        tokenizer_name = model_name if tokenizer_name is None else tokenizer_name
        tokenizer = load_correct_tokenizer(
            tokenizer_name = tokenizer_name,
            model_max_length = max_position_embeddings,
            padding_side = "right",
            token = token,
            trust_remote_code = trust_remote_code,
            fix_tokenizer = fix_tokenizer,
        )

        model, tokenizer = patch_tokenizer(model, tokenizer)
        model, tokenizer = model_patcher.post_patch(
            model, tokenizer, correct_dtype = dtype
        )

        # Patch up QKV / O and MLP
        for idx, layer in enumerate(model.model.layers):
            layer.self_attn.apply_qkv = original_apply_qkv
            layer.self_attn.apply_o = original_apply_o

        # Patch Trainer
        from transformers.trainer import Trainer

        try:
            if Trainer._inner_training_loop.__name__ != "_fast_inner_training_loop":
                inner_training_loop = inspect.getsource(Trainer._inner_training_loop)
                Trainer._original_training_loop = inner_training_loop
            else:
                inner_training_loop = Trainer._original_training_loop
        except:
            raise RuntimeError("Unsloth: Unsuccessfully patched inner_training_loop")

        import transformers.trainer

        items_in_trainer = dir(transformers.trainer)
        good_items = []
        for item in items_in_trainer:
            if item in inner_training_loop:
                good_items.append(item)
        exec(
            "from transformers.trainer import ("
            + ", ".join(x for x in good_items)
            + ")",
            globals(),
        )

        start = re.search(
            r"logger\.info\([\"\'].+?Running training", inner_training_loop
        ).span(0)[0]
        end = inner_training_loop.find("\n\n", start)
        original_debug = inner_training_loop[start:end]
        spaces = re.search(r"\n([\s\t]{1,})", original_debug).group(0)[1:]
        front_spaces = re.match(r"([\s\t]{1,})", inner_training_loop).group(0)

        # Cannot use \\ since it will cause a SyntaxWarning in Python 3.12
        # Instead use chr(92) == \\
        debug_info = """debug_info = \\
        f"==((====))==  Unsloth - 2x faster free finetuning | Num GPUs used = {len(set(p.device for p in model.parameters()))}\\n"\\
        f"   {chr(92)}{chr(92)}   /|    Num examples = {num_examples:,} | Num Epochs = {num_train_epochs:,} | Total steps = {max_steps:,}\\n"\\
        f"O^O/ {chr(92)}_/ {chr(92)}    Batch size per device = {self._train_batch_size:,} | Gradient accumulation steps = {args.gradient_accumulation_steps}\\n"\\
        f"{chr(92)}        /    Data Parallel GPUs = {args.world_size} | Total batch size ({self._train_batch_size} x {args.gradient_accumulation_steps} x {args.world_size}) = {total_train_batch_size:,}\\n"\\
        f' "-____-"     Trainable parameters = {get_model_param_count(model, trainable_only=True):,} of {get_model_param_count(model):,} ({get_model_param_count(model, trainable_only=True)/get_model_param_count(model)*100:.2f}% trained)'
        logger.warning(debug_info)
        import gc
        for _ in range(3):
            gc.collect()
            if DEVICE_TYPE == "xpu":
                torch.xpu.empty_cache()
            else:
                torch.cuda.empty_cache()"""

        debug_info = debug_info.split("\n")
        debug_info = "\n".join(
            [debug_info[0]] + [spaces + x[8:] for x in debug_info[1:]]
        )
        inner_training_loop = inner_training_loop.replace(original_debug, debug_info)

        debug_info = """n_total_devices = total_train_batch_size // \\
            args.gradient_accumulation_steps // self._train_batch_size
        if n_total_devices > 1:
            logger.warning_once('Unsloth is running with multi GPUs - the effective batch size is multiplied by ' + str(n_total_devices))
        debug_info ="""
        debug_info = debug_info.split("\n")
        debug_info = "\n".join(
            [debug_info[0]] + [spaces + x[8:] for x in debug_info[1:]]
        )
        inner_training_loop = inner_training_loop.replace("debug_info =", debug_info, 1)

        front_spaces = re.match(r"[\t\s]{1,}", inner_training_loop).group(0)
        inner_training_loop = re.sub(
            r"^" + front_spaces, "", inner_training_loop, flags = re.MULTILINE
        )
        inner_training_loop = inner_training_loop.replace(
            "train_dataloader = tpu_spmd_dataloader(train_dataloader)",
            "raise RuntimeError('Unsloth: TPUs are not yet supported!')",
        )
        inner_training_loop = inner_training_loop.replace(
            "_inner_training_loop",
            "_fast_inner_training_loop",
            1,
        )
        inner_training_loop = inner_training_loop.replace(
            "is_torch_tpu_available()",
            "False",
        )
        exec(inner_training_loop, globals())
        Trainer._inner_training_loop = _fast_inner_training_loop

        # Save max_seq_length
        model.max_seq_length = max_seq_length
        m = model
        while hasattr(m, "model"):
            m.max_seq_length = max_seq_length
            m = m.model
        m.max_seq_length = max_seq_length
        # Save to modules as well
        for module in model.modules():
            module.max_seq_length = max_seq_length

        # We check the tokenizer first for errors
        if fix_tokenizer:
            tokenizer = check_tokenizer(
                model = model,
                tokenizer = tokenizer,
                model_name = model_name,
                model_max_length = max_position_embeddings,
                padding_side = "right",
                token = token,
            )
        patch_saving_functions(tokenizer)

        # Fix up config for transformers uploading PEFT
        # Not necessary anymore since we require transformers>=4.37!
        if False:
            name = model.config._name_or_path
            if name.startswith("unsloth/") and name.endswith("-bnb-4bit"):
                name = name[: len(name) - len("-bnb-4bit")]
                model.config.update({"_name_or_path": name})

        # Log Unsloth version for future fastpaths for inference
        model.config.update({"unsloth_version": __version__})

        # Add save modules
        patch_saving_functions(model)
        Trainer._inner_training_loop = _fast_inner_training_loop

        # Fix gradient accumulation. See issue #4982.
        apply_accepts_loss_kwargs_fix(model)
        patch_gradient_accumulation_fix(Trainer)

        # Save tokenizer for inference purposes
        tokenizer.padding_side = "left"  # Force inference
        internal_model = model
        while hasattr(internal_model, "model"):
            internal_model._saved_temp_tokenizer = tokenizer
            # Also set is_loaded_in_8bit to disable incorrect DDP
            internal_model.is_loaded_in_8bit = True

            internal_model = internal_model.model
        internal_model._saved_temp_tokenizer = tokenizer
        # Also set is_loaded_in_8bit to disable incorrect DDP
        internal_model.is_loaded_in_8bit = True

        # For transformers > 4.47.1, we need to add rotary_emb to all attention layers
        if IS_ATTENTION_REFACTOR or hasattr(model.model, "rotary_emb"):
            rotary_emb = model.model.rotary_emb
            for layer in model.model.layers:
                layer.self_attn.rotary_emb = rotary_emb

        # Add for_inference and for_training
        model.for_training = functools.partial(FastLlamaModel.for_training, model)
        model.for_inference = functools.partial(FastLlamaModel.for_inference, model)
        m = model
        while hasattr(m, "model"):
            m.for_training = functools.partial(FastBaseModel.for_training, m)
            m.for_inference = functools.partial(FastBaseModel.for_inference, m)
            m = m.model

        # Patch generate
        is_classification = "Classification" in str(type(model))
        if not is_classification and model.generate.__name__ != "unsloth_fast_generate":
            model._old_generate = model.generate
            unsloth_fast_generate.__doc__ = model._old_generate.__doc__
            model.generate = types.MethodType(unsloth_fast_generate, model)
        # Set weight[padding_idx] = 0 for embeddings that are NOT tied with the
        # lm_head. When weights are tied, zeroing the padding row also zeros
        # the corresponding lm_head row, forcing logit = 0 for the pad token.
        # This is higher than the (negative) logits for real tokens in models
        # like Gemma, causing the decoder to emit <pad> and produce gibberish.
        # Skip entirely if eos_token == pad_token to avoid zeroing EOS embedding.
        eos_token_id = (
            getattr(tokenizer, "eos_token_id", None) if tokenizer is not None else None
        )
        pad_token_id = (
            getattr(tokenizer, "pad_token_id", None) if tokenizer is not None else None
        )
        if tokenizer is not None and eos_token_id != pad_token_id:
            lm_head = getattr(model, "lm_head", None)
            lm_head_weight = (
                getattr(lm_head, "weight", None) if lm_head is not None else None
            )
            with torch.no_grad():
                for name, module in model.named_modules():
                    if type(module) is torch.nn.Embedding:
                        if (
                            getattr(module, "weight", None) is not None
                            and getattr(module, "padding_idx", None) is not None
                        ):
                            if module.padding_idx < module.weight.shape[0]:
                                # Skip if tied to lm_head
                                if (
                                    lm_head_weight is not None
                                    and module.weight.data_ptr()
                                    == lm_head_weight.data_ptr()
                                ):
                                    continue
                                module.weight[module.padding_idx] = 0
        return model, tokenizer