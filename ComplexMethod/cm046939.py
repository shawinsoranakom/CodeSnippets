def from_pretrained(
        model_name,
        max_seq_length = None,
        dtype = None,
        load_in_4bit = False,  # Changed default: 4-bit is slow for encoders
        load_in_8bit = False,
        load_in_16bit = True,  # Changed default: 16-bit is optimal for encoders
        full_finetuning = False,
        token = None,
        device_map = "sequential",
        rope_scaling = None,
        fix_tokenizer = True,
        trust_remote_code = False,
        use_gradient_checkpointing = False,  # Changed default: conflicts with torch.compile
        resize_model_vocab = None,
        revision = None,
        use_exact_model_name = False,
        offload_embedding = False,
        random_state = 3407,
        max_lora_rank = 64,
        disable_log_stats = True,
        qat_scheme = None,
        unsloth_tiled_mlp = False,
        pooling_mode = "mean",
        for_inference = False,
        **kwargs,
    ):
        try:
            from sentence_transformers import SentenceTransformer
            from sentence_transformers.models import Transformer, Pooling, Normalize
        except ImportError:
            raise ImportError(
                "Unsloth: To use `FastSentenceTransformer`, you must install `sentence-transformers`.\n"
                "Run `pip install sentence-transformers` to install it."
            )

        # if for_inference == True, skip Unsloth optimizations to avoid torch compile issues
        if for_inference:
            st_device = device_map
            if isinstance(st_device, dict) or (
                isinstance(st_device, str) and st_device in ["auto", "sequential"]
            ):
                st_device = None

            # this was added because when loading for inference it was defaulting to float32
            # propagate dtype to model_kwargs, default to "auto"
            model_kwargs = kwargs.get("model_kwargs", {})
            model_kwargs["dtype"] = dtype if dtype is not None else "auto"

            # filter kwargs for SentenceTransformer
            st_kwargs = {
                "device": st_device,
                "trust_remote_code": trust_remote_code,
                "token": token,
                "revision": revision,
                "model_kwargs": model_kwargs,
            }

            # add other known kwargs if present
            known_keys = [
                "cache_folder",
                "truncate_dim",
                "tokenizer_kwargs",
                "config_kwargs",
            ]
            for k in known_keys:
                if k in kwargs:
                    st_kwargs[k] = kwargs[k]

            st_model = SentenceTransformer(model_name, **st_kwargs)
            return st_model

        # sanity check, thanks Etherl:
        if full_finetuning and (load_in_4bit or load_in_8bit):
            print(
                "Unsloth: You selected full finetuning support, but 4bit / 8bit is enabled - disabling LoRA / QLoRA."
            )
            load_in_4bit = False
            load_in_8bit = False
            load_in_fp8 = False
            load_in_16bit = False

        if int(load_in_4bit) + int(load_in_8bit) + int(load_in_16bit) >= 2:
            raise RuntimeError(
                "Unsloth: Can only load in 4bit or 8bit or 16bit, not a combination!\n"
                "Also, we by default set `load_in_16bit = True`.\n"
                "If you want 4bit LoRA finetuning, set `load_in_16bit = False` and `load_in_4bit = True`\n"
                "If you want 8bit finetuning, set both `load_in_16bit = False` and `load_in_8bit = True`"
            )

        if "auto_model" not in kwargs:
            kwargs["auto_model"] = AutoModel

        transformers4 = Version(transformers.__version__).major < 5
        model_type = ""
        config = None
        try:
            config = AutoConfig.from_pretrained(
                model_name, token = token, trust_remote_code = trust_remote_code
            )
            model_type = getattr(config, "model_type", "")
        except:
            pass

        # Fast encoder path: Use native torch.compile for encoder models (6x speedup)
        # This bypasses Unsloth's auto-compiler which adds @torch.compiler.disable decorators
        # that interfere with torch.compile and cause runtime errors for encoder models.
        # NOTE: The old Unsloth path is BROKEN for encoder models with torch 2.9+ due to
        # conflicting @torch.compile and @torch.compiler.disable decorators.
        # Set UNSLOTH_COMPILE_DISABLE=1 to disable torch.compile and use the old path.
        is_encoder_model = (
            model_type.lower() in FastSentenceTransformer.ENCODER_MODEL_TYPES
        )
        use_fast_encoder = os.environ.get("UNSLOTH_COMPILE_DISABLE", "0") != "1"
        if use_fast_encoder and is_encoder_model:
            # torch.compile mode: "default" is safest for PEFT/LoRA training
            # Note: "reduce-overhead" uses CUDA Graphs which is incompatible with PEFT
            compile_mode = "default"

            # Determine dtype - handle float16 machines that don't support bfloat16
            if dtype is None:
                if load_in_16bit:
                    dtype = torch.float16 if not SUPPORTS_BFLOAT16 else torch.bfloat16
                else:
                    dtype = torch.float32
            elif dtype == torch.bfloat16 and not SUPPORTS_BFLOAT16:
                print(
                    "Unsloth: Device does not support bfloat16. Using float16 instead."
                )
                dtype = torch.float16

            # Determine device
            st_device = device_map
            if isinstance(st_device, dict) or (
                isinstance(st_device, str) and st_device in ["auto", "sequential"]
            ):
                st_device = "cuda"

            # Build model_kwargs for SentenceTransformer
            model_kwargs = {"torch_dtype": dtype}

            encoder_attn_impl = resolve_encoder_attention_implementation(
                kwargs.get("auto_model", AutoModel),
                config,
                model_type = model_type,
                disable_sdpa_model_names = DISABLE_SDPA_MODEL_NAMES,
            )
            supports_sdpa = encoder_attn_impl == "sdpa"
            if encoder_attn_impl is not None:
                model_kwargs["attn_implementation"] = encoder_attn_impl

            # Print optimization status
            sdpa_str = " + SDPA" if supports_sdpa else ""
            if load_in_4bit:
                print(
                    f"Unsloth: Using fast encoder path for {model_type} with 4-bit quantization{sdpa_str}"
                )
            else:
                print(
                    f"Unsloth: Using fast encoder path for {model_type} (torch.compile{sdpa_str})"
                )

            # Handle 4-bit quantization via BitsAndBytesConfig
            if load_in_4bit:
                from transformers import BitsAndBytesConfig

                bnb_config = BitsAndBytesConfig(
                    load_in_4bit = True,
                    bnb_4bit_compute_dtype = dtype,
                    bnb_4bit_quant_type = "nf4",
                    bnb_4bit_use_double_quant = True,
                )
                model_kwargs["quantization_config"] = bnb_config
                # When using quantization, device must be handled by accelerate
                st_device = None

            # Handle gradient checkpointing - warn user it conflicts with torch.compile
            _use_gc = use_gradient_checkpointing
            if _use_gc and _use_gc != False:
                print(
                    "Unsloth Warning: Gradient checkpointing is incompatible with torch.compile."
                )
                print("Disabling torch.compile to enable gradient checkpointing.")
                compile_mode = None  # Disable compilation

                is_mpnet = "mpnet" == model_type.lower()

                if is_mpnet and transformers4:
                    FastSentenceTransformer._patch_mpnet_v4()
                elif is_mpnet:
                    FastSentenceTransformer._patch_mpnet_v5()

            # Load via native SentenceTransformer (bypasses Unsloth patching)
            st_model = SentenceTransformer(
                model_name,
                device = st_device,
                trust_remote_code = trust_remote_code,
                token = token,
                revision = revision,
                model_kwargs = model_kwargs,
            )

            # Store metadata for get_peft_model
            st_model._unsloth_fast_encoder = True
            st_model._compile_mode = compile_mode
            st_model._dtype = dtype
            st_model._load_in_4bit = load_in_4bit
            st_model.no_modules = False

            # Add save methods
            def _save_pretrained_merged(self, save_directory, **save_kwargs):
                self.save_pretrained(save_directory)
                tokenizer = save_kwargs.pop("tokenizer", self.tokenizer)
                if hasattr(self[0], "auto_model"):
                    inner = self[0].auto_model
                    # Handle compiled model
                    if hasattr(inner, "_orig_mod"):
                        inner = inner._orig_mod
                    if hasattr(inner, "merge_and_unload"):
                        merged = inner.merge_and_unload()
                        merged.save_pretrained(save_directory)
                    elif hasattr(inner, "save_pretrained"):
                        inner.save_pretrained(save_directory)
                if tokenizer is not None:
                    tokenizer.save_pretrained(save_directory)
                FastSentenceTransformer._add_unsloth_branding(save_directory)

            st_model.save_pretrained_merged = types.MethodType(
                _save_pretrained_merged, st_model
            )

            st_model.save_pretrained_torchao = types.MethodType(
                _save_pretrained_torchao, st_model
            )

            st_model.save_pretrained_gguf = types.MethodType(
                _save_pretrained_gguf, st_model
            )

            st_model.push_to_hub_gguf = types.MethodType(_push_to_hub_gguf, st_model)

            def _push_to_hub_merged(self, repo_id, **push_kwargs):
                hub_token = push_kwargs.get("token", None) or get_token()
                if hub_token is None:
                    raise ValueError("No HF token provided")
                api = HfApi(token = hub_token)
                try:
                    api.create_repo(
                        repo_id = repo_id,
                        private = push_kwargs.get("private"),
                        exist_ok = True,
                        repo_type = "model",
                    )
                except:
                    pass
                FastSentenceTransformer._add_unsloth_tags(repo_id, hub_token)
                with tempfile.TemporaryDirectory() as temp_dir:
                    self.save_pretrained_merged(temp_dir, **push_kwargs)
                    api.upload_folder(
                        folder_path = temp_dir,
                        repo_id = repo_id,
                        commit_message = push_kwargs.get(
                            "commit_message", "Upload model"
                        ),
                    )
                print(f"Unsloth: Pushed to https://huggingface.co/{repo_id}")

            st_model.push_to_hub_merged = types.MethodType(
                _push_to_hub_merged, st_model
            )

            return st_model

        # Warn if using 4-bit with encoder (slow due to dequantization overhead)
        if is_encoder_model and load_in_4bit:
            print(
                "Unsloth Warning: 4-bit quantization adds ~2.3x overhead for encoder models."
            )
            print("Consider using load_in_16bit=True for better performance.")

        # check if the model supports add_pooling_layer
        if "add_pooling_layer" not in kwargs:
            supported = FastSentenceTransformer._has_add_pooling_layer(
                config, kwargs.get("auto_model", AutoModel)
            )
            if supported:
                kwargs["add_pooling_layer"] = False

        # forces fp8 to be False since it's not supported
        fp8 = kwargs.pop("load_in_fp8", None)
        if fp8:
            logging.info("Unsloth: Disabling fp8 for model")
        load_in_fp8 = False

        # this is a fix for Snowflake/snowflake-arctic-embed-l-v2.0
        # it has pooler weights which we don't care about for training,
        # however unsloth throws an exception if "UNSLOTH_WARN_UNINITIALIZED" == 1 and it sees unused weights
        old_environ = os.environ.get("UNSLOTH_WARN_UNINITIALIZED", "1")
        os.environ["UNSLOTH_WARN_UNINITIALIZED"] = "0"

        is_distilbert = "distilbert" == model_type.lower()
        is_mpnet = "mpnet" == model_type.lower()

        if is_distilbert and transformers4:
            FastSentenceTransformer._patch_distilbert_v4()
        elif is_distilbert:
            FastSentenceTransformer._patch_distilbert_v5()
        elif is_mpnet and transformers4:
            FastSentenceTransformer._patch_mpnet_v4()
        elif is_mpnet:
            FastSentenceTransformer._patch_mpnet_v5()

        # check if modules.json exists - if not, force 16-bit training
        # why? because i have to implement saving myself for these models, and i don't feel like adding dequantization
        # to the save_pretrained_merged for a model that really should be trained in 16-bit anyway
        has_modules_json = (
            FastSentenceTransformer._module_path(model_name, token) is not None
        )

        if not has_modules_json and load_in_4bit:
            print(
                "Unsloth: No modules.json found. This is not a sentence-transformers model.\n"
                "Forcing 16-bit loading to simplify merged model saving."
            )
            load_in_4bit = False
            load_in_16bit = True

        try:
            model, tokenizer = FastModel.from_pretrained(
                model_name = model_name,
                max_seq_length = max_seq_length,
                dtype = dtype,
                load_in_4bit = load_in_4bit,
                load_in_8bit = load_in_8bit,
                load_in_16bit = load_in_16bit,
                full_finetuning = full_finetuning,
                token = token,
                device_map = device_map,
                rope_scaling = rope_scaling,
                fix_tokenizer = fix_tokenizer,
                trust_remote_code = trust_remote_code,
                use_gradient_checkpointing = use_gradient_checkpointing,
                resize_model_vocab = resize_model_vocab,
                revision = revision,
                return_logits = False,
                use_exact_model_name = use_exact_model_name,
                offload_embedding = offload_embedding,
                random_state = random_state,
                max_lora_rank = max_lora_rank,
                disable_log_stats = disable_log_stats,
                qat_scheme = qat_scheme,
                load_in_fp8 = load_in_fp8,
                unsloth_tiled_mlp = unsloth_tiled_mlp,
                **kwargs,
            )
        finally:
            os.environ["UNSLOTH_WARN_UNINITIALIZED"] = old_environ

        # try to load modules, otherwise fallback to old hard-coded modules
        from sentence_transformers import SentenceTransformer

        modules, no_modules = FastSentenceTransformer._load_modules(
            model_name,
            token,
            model,
            tokenizer,
            max_seq_length,
            pooling_mode,
            trust_remote_code = trust_remote_code,
        )

        st_device = device_map
        if isinstance(st_device, dict) or (
            isinstance(st_device, str) and st_device in ["auto", "sequential"]
        ):
            st_device = None

        st_model = SentenceTransformer(modules = modules, device = st_device)
        st_model.no_modules = no_modules

        def _save_pretrained_merged(self, save_directory, **kwargs):
            # check which adapter files exist before save_pretrained
            adapter_files = ["adapter_model.safetensors", "adapter_config.json"]
            existing_before = {
                f
                for f in adapter_files
                if os.path.exists(os.path.join(save_directory, f))
            }

            # sentence-transformers config and modules only get saved if we call save_pretrained
            self.save_pretrained(save_directory)

            # remove LoRA adapters only if they were created by save_pretrained (not pre-existing)
            for file in adapter_files:
                if file not in existing_before:
                    try:
                        os.remove(os.path.join(save_directory, file))
                    except:
                        pass

            tokenizer = kwargs.pop("tokenizer", self.tokenizer)
            if self.no_modules:
                # fallback for non-sentence-transformers models
                print(
                    "Unsloth: No modules detected. Using standard merge_and_unload for saving..."
                )
                safe_kwargs = kwargs.copy()
                # filter out Unsloth-specific args that are not in huggingface's save_pretrained
                unsloth_args = [
                    "save_method",
                    "temporary_location",
                    "maximum_memory_usage",
                ]
                for k in unsloth_args:
                    safe_kwargs.pop(k, None)

                merged_model = self[0].auto_model.merge_and_unload()
                merged_model.save_pretrained(save_directory, **safe_kwargs)
                if tokenizer is not None:
                    tokenizer.save_pretrained(save_directory)
            else:
                self[0].auto_model.save_pretrained_merged(
                    save_directory, tokenizer = tokenizer, **kwargs
                )

            # add Unsloth branding to the generated README
            try:
                FastSentenceTransformer._add_unsloth_branding(save_directory)
            except Exception as e:
                print(f"Unsloth Warning: Failed to add branding to README: {e}")

        st_model.save_pretrained_merged = types.MethodType(
            _save_pretrained_merged, st_model
        )

        st_model.save_pretrained_torchao = types.MethodType(
            _save_pretrained_torchao, st_model
        )

        st_model.save_pretrained_gguf = types.MethodType(
            _save_pretrained_gguf, st_model
        )

        st_model.push_to_hub_gguf = types.MethodType(_push_to_hub_gguf, st_model)

        def _push_to_hub_merged(self, repo_id, **kwargs):
            token = kwargs.get("token", None) or get_token()
            if token is None:
                raise ValueError(
                    "No HF token provided. Please provide a token or login with `hf auth login`"
                )
            private = kwargs.get("private", None)
            commit_message = kwargs.get("commit_message", "Upload model")

            from huggingface_hub import HfApi

            api = HfApi(token = token)
            try:
                api.create_repo(
                    repo_id = repo_id,
                    private = private,
                    exist_ok = True,
                    repo_type = "model",
                )
            except:
                pass

            # order doesn't seem to matter for this after repo creation...
            FastSentenceTransformer._add_unsloth_tags(repo_id, token)

            with tempfile.TemporaryDirectory() as temp_dir:
                self.save_pretrained_merged(temp_dir, **kwargs)
                api.upload_folder(
                    folder_path = temp_dir,
                    repo_id = repo_id,
                    commit_message = commit_message,
                )
            print(
                f"Unsloth: Successfully pushed merged model to https://huggingface.co/{repo_id}"
            )

        st_model.push_to_hub_merged = types.MethodType(_push_to_hub_merged, st_model)
        return st_model