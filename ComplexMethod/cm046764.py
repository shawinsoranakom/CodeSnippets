def from_identifier(
        cls,
        model_id: str,
        hf_token: Optional[str] = None,
        is_lora: bool = False,
        gguf_variant: Optional[str] = None,
    ) -> Optional["ModelConfig"]:
        """
        Create ModelConfig from a clean model identifier.

        For FastAPI routes where the frontend sends sanitized model paths.
        No Gradio dropdown parsing - expects clean identifiers like:
        - "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"
        - "./outputs/my_lora_adapter"
        - "/absolute/path/to/model"

        Args:
            model_id: Clean model identifier (HF repo name or local path)
            hf_token: Optional HF token for vision detection on gated models
            is_lora: Whether this is a LoRA adapter
            gguf_variant: Optional GGUF quantization variant (e.g. "Q4_K_M").
                For remote GGUF repos, specifies which quant to load via -hf.
                If None, auto-selects using _pick_best_gguf().

        Returns:
            ModelConfig or None if configuration cannot be created
        """
        if not model_id or not model_id.strip():
            return None

        identifier = model_id.strip()
        is_local = is_local_path(identifier)
        path = normalize_path(identifier) if is_local else identifier

        # Add unsloth/ prefix for shorthand HF models
        if not is_local and "/" not in identifier:
            identifier = f"unsloth/{identifier}"
            path = identifier

        # Preserve requested casing, but if a case-variant already exists in local HF cache,
        # reuse that exact repo_id spelling to avoid one-time re-downloads after #2592.
        if not is_local:
            resolved_identifier = resolve_cached_repo_id_case(identifier)
            if resolved_identifier != identifier:
                logger.info(
                    "Using cached repo_id casing '%s' for requested '%s'",
                    resolved_identifier,
                    identifier,
                )
                identifier = resolved_identifier
                path = resolved_identifier

        # Auto-detect GGUF models (check before LoRA/vision detection)
        if is_local:
            if gguf_variant:
                gguf_file = _find_local_gguf_by_variant(path, gguf_variant)
            else:
                gguf_file = detect_gguf_model(path)
            if gguf_file:
                display_name = Path(gguf_file).stem
                logger.info(f"Detected local GGUF model: {gguf_file}")

                # Detect vision: check if base model is vision, then look for mmproj
                mmproj_file = None
                gguf_is_vision = False
                gguf_dir = Path(gguf_file).parent

                # Determine if this is a vision model from export metadata
                base_is_vision = False
                meta_path = gguf_dir / "export_metadata.json"
                if meta_path.exists():
                    try:
                        meta = json.loads(meta_path.read_text())
                        base = meta.get("base_model")
                        if base and is_vision_model(base, hf_token = hf_token):
                            base_is_vision = True
                            logger.info(f"GGUF base model '{base}' is a vision model")
                    except Exception as e:
                        logger.debug(f"Could not read export metadata: {e}")

                # If vision (or mmproj happens to exist), find the mmproj
                # file. The recursive variant scan in
                # ``_find_local_gguf_by_variant`` may have returned a
                # weight file inside a quant-named subdir (e.g.
                # ``.../BF16/foo.gguf``) while ``mmproj-*.gguf`` lives
                # at the snapshot root. Pass ``search_root=path`` so
                # ``detect_mmproj_file`` walks up to the snapshot root
                # instead of seeing only the weight file's immediate
                # parent.
                mmproj_file = detect_mmproj_file(gguf_file, search_root = path)
                if mmproj_file:
                    gguf_is_vision = True
                    logger.info(f"Detected mmproj for vision: {mmproj_file}")
                elif base_is_vision:
                    logger.warning(
                        f"Base model is vision but no mmproj file found in {gguf_dir}"
                    )

                return cls(
                    identifier = identifier,
                    display_name = display_name,
                    path = path,
                    is_local = True,
                    is_cached = True,
                    is_vision = gguf_is_vision,
                    is_lora = False,
                    is_gguf = True,
                    gguf_file = gguf_file,
                    gguf_mmproj_file = mmproj_file,
                )
        else:
            # Check if the HF repo contains GGUF files
            gguf_filename = detect_gguf_model_remote(identifier, hf_token = hf_token)
            if gguf_filename:
                # Preflight: verify llama-server binary exists BEFORE user waits
                # for a multi-GB download that llama-server handles natively
                from core.inference.llama_cpp import LlamaCppBackend

                if not LlamaCppBackend._find_llama_server_binary():
                    raise RuntimeError(
                        "llama-server binary not found — cannot load GGUF models. "
                        "Run setup.sh to build it, or set LLAMA_SERVER_PATH."
                    )

                # Use list_gguf_variants() to detect vision & resolve variant
                variants, has_vision = list_gguf_variants(identifier, hf_token = hf_token)
                variant = gguf_variant
                if not variant:
                    # Auto-select best quantization
                    variant_filenames = [v.filename for v in variants]
                    best = _pick_best_gguf(variant_filenames)
                    if best:
                        variant = _extract_quant_label(best)
                    else:
                        variant = "Q4_K_M"  # Fallback — llama-server's own default

                display_name = f"{identifier.split('/')[-1]} ({variant})"
                logger.info(
                    f"Detected remote GGUF repo '{identifier}', "
                    f"variant={variant}, vision={has_vision}"
                )
                return cls(
                    identifier = identifier,
                    display_name = display_name,
                    path = identifier,
                    is_local = False,
                    is_cached = False,
                    is_vision = has_vision,
                    is_lora = False,
                    is_gguf = True,
                    gguf_file = None,
                    gguf_hf_repo = identifier,
                    gguf_variant = variant,
                )

        # Auto-detect LoRA for local paths (check adapter_config.json on disk)
        if not is_lora and is_local:
            detected_base = (
                get_base_model_from_lora(path)
                if _looks_like_lora_adapter(Path(path))
                else None
            )
            if detected_base:
                is_lora = True
                logger.info(
                    f"Auto-detected local LoRA adapter at '{path}' (base: {detected_base})"
                )

        # Auto-detect LoRA for remote HF models (check repo file listing)
        if not is_lora and not is_local:
            try:
                from huggingface_hub import model_info as hf_model_info

                info = hf_model_info(identifier, token = hf_token)
                repo_files = [s.rfilename for s in info.siblings]
                if "adapter_config.json" in repo_files:
                    is_lora = True
                    logger.info(f"Auto-detected remote LoRA adapter: '{identifier}'")
            except Exception as e:
                logger.debug(
                    f"Could not check remote LoRA status for '{identifier}': {e}"
                )

        # Handle LoRA adapters
        base_model = None
        if is_lora:
            if is_local:
                # Local LoRA: read adapter_config.json from disk
                base_model = get_base_model_from_lora(path)
            else:
                # Remote LoRA: download adapter_config.json from HF
                try:
                    from huggingface_hub import hf_hub_download

                    config_path = hf_hub_download(
                        identifier, "adapter_config.json", token = hf_token
                    )
                    with open(config_path, "r") as f:
                        adapter_config = json.load(f)
                    base_model = adapter_config.get("base_model_name_or_path")
                    if base_model:
                        logger.info(f"Resolved remote LoRA base model: '{base_model}'")
                except Exception as e:
                    logger.warning(
                        f"Could not download adapter_config.json for '{identifier}': {e}"
                    )

            if not base_model:
                logger.warning(f"Could not determine base model for LoRA '{path}'")
                return None
            check_model = base_model
        else:
            check_model = identifier

        vision = is_vision_model(check_model, hf_token = hf_token)
        audio_type_val = detect_audio_type(check_model, hf_token = hf_token)
        has_audio_in = is_audio_input_type(audio_type_val)

        display_name = Path(path).name if is_local else identifier.split("/")[-1]

        return cls(
            identifier = identifier,
            display_name = display_name,
            path = path,
            is_local = is_local,
            is_cached = is_model_cached(identifier) if not is_local else True,
            is_vision = vision,
            is_lora = is_lora,
            is_audio = audio_type_val is not None and audio_type_val != "audio_vlm",
            audio_type = audio_type_val,
            has_audio_input = has_audio_in,
            base_model = base_model,
        )