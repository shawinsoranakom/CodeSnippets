def _handle_load(backend, config: dict, resp_queue: Any) -> None:
    """Handle a load command: load a model into the backend."""
    try:
        mc = _build_model_config(config)

        hf_token = config.get("hf_token")
        hf_token = hf_token if hf_token and hf_token.strip() else None

        # Auto-detect quantization for LoRA adapters
        load_in_4bit = config.get("load_in_4bit", True)
        if mc.is_lora and mc.path:
            import json
            from pathlib import Path

            adapter_cfg_path = Path(mc.path) / "adapter_config.json"
            if adapter_cfg_path.exists():
                try:
                    with open(adapter_cfg_path) as f:
                        adapter_cfg = json.load(f)
                    training_method = adapter_cfg.get("unsloth_training_method")
                    if training_method == "lora" and load_in_4bit:
                        logger.info(
                            "adapter_config.json says lora — setting load_in_4bit=False"
                        )
                        load_in_4bit = False
                    elif training_method == "qlora" and not load_in_4bit:
                        logger.info(
                            "adapter_config.json says qlora — setting load_in_4bit=True"
                        )
                        load_in_4bit = True
                    elif not training_method:
                        if (
                            mc.base_model
                            and "-bnb-4bit" not in mc.base_model.lower()
                            and load_in_4bit
                        ):
                            logger.info(
                                "No training method, base model has no -bnb-4bit — setting load_in_4bit=False"
                            )
                            load_in_4bit = False
                except Exception as e:
                    logger.warning("Could not read adapter_config.json: %s", e)

        # Auto-enable trust_remote_code for NemotronH/Nano models only.
        # NemotronH has config parsing bugs requiring trust_remote_code=True.
        # Other transformers 5.x models are native and do NOT need it.
        # NOTE: Must NOT match Llama-Nemotron (standard Llama architecture).
        _NEMOTRON_TRUST_SUBSTRINGS = ("nemotron_h", "nemotron-h", "nemotron-3-nano")
        trust_remote_code = config.get("trust_remote_code", False)
        if not trust_remote_code:
            model_name = config["model_name"]
            _mn_lower = model_name.lower()
            if any(sub in _mn_lower for sub in _NEMOTRON_TRUST_SUBSTRINGS) and (
                _mn_lower.startswith("unsloth/") or _mn_lower.startswith("nvidia/")
            ):
                trust_remote_code = True
                logger.info(
                    "Auto-enabled trust_remote_code for Nemotron model: %s",
                    model_name,
                )

        # Send heartbeats every 30s so the orchestrator knows we're still alive
        # (download / weight loading can take a long time on slow connections)
        xet_disabled = os.environ.get("HF_HUB_DISABLE_XET") == "1"

        # Watch both the model repo and base model repo (for LoRA loads
        # where the base model download is the actual bottleneck)
        watch_repos = [mc.identifier]
        base = getattr(mc, "base_model", None)
        if base and str(base) != mc.identifier:
            watch_repos.append(str(base))

        heartbeat_stop = _start_heartbeat(
            resp_queue,
            interval = 30.0,
            xet_disabled = xet_disabled,
            model_names = watch_repos,
        )
        try:
            success = backend.load_model(
                config = mc,
                max_seq_length = config.get("max_seq_length", 2048),
                load_in_4bit = load_in_4bit,
                hf_token = hf_token,
                trust_remote_code = trust_remote_code,
                gpu_ids = config.get("resolved_gpu_ids"),
            )
        finally:
            heartbeat_stop.set()

        if success:
            # Build model_info for the parent to mirror
            model_info = {
                "identifier": mc.identifier,
                "display_name": mc.display_name,
                "is_vision": mc.is_vision,
                "is_lora": mc.is_lora,
                "is_gguf": False,
                "is_audio": getattr(mc, "is_audio", False),
                "audio_type": getattr(mc, "audio_type", None),
                "has_audio_input": getattr(mc, "has_audio_input", False),
            }
            _send_response(
                resp_queue,
                {
                    "type": "loaded",
                    "success": True,
                    "model_info": model_info,
                    "ts": time.time(),
                },
            )
        else:
            _send_response(
                resp_queue,
                {
                    "type": "loaded",
                    "success": False,
                    "error": "Failed to load model",
                    "ts": time.time(),
                },
            )

    except Exception as exc:
        _send_response(
            resp_queue,
            {
                "type": "loaded",
                "success": False,
                "error": str(exc),
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            },
        )