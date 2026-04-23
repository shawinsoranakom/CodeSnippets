def load_model(
        self,
        config,  # ModelConfig
        max_seq_length: int = 2048,
        dtype = None,
        load_in_4bit: bool = True,
        hf_token: Optional[str] = None,
        trust_remote_code: bool = False,
        gpu_ids: Optional[list[int]] = None,
    ) -> bool:
        """Load a model for inference.

        Always spawns a fresh subprocess for each model load. This ensures
        a clean Python interpreter — no stale unsloth patches, torch.compile
        caches, or inspect.getsource() failures from a previous model.
        """
        from utils.transformers_version import needs_transformers_5

        model_name = config.identifier
        self.loading_models.add(model_name)

        try:
            needed_major = "5" if needs_transformers_5(model_name) else "4"

            # Build config dict for subprocess
            sub_config = {
                "model_name": model_name,
                "max_seq_length": max_seq_length,
                "load_in_4bit": load_in_4bit,
                "hf_token": hf_token or "",
                "gguf_variant": getattr(config, "gguf_variant", None),
                "trust_remote_code": trust_remote_code,
                "gpu_ids": gpu_ids,
            }
            resolved_gpu_ids, gpu_selection = prepare_gpu_selection(
                gpu_ids,
                model_name = model_name,
                hf_token = hf_token,
                load_in_4bit = load_in_4bit,
            )
            sub_config["resolved_gpu_ids"] = resolved_gpu_ids
            sub_config["gpu_selection"] = gpu_selection

            # Always kill existing subprocess and spawn fresh.
            # Reusing a subprocess after unsloth patches torch internals
            # causes inspect.getsource() failures on the next model load.
            if self._ensure_subprocess_alive():
                self._cancel_generation()
                time.sleep(0.3)
                self._shutdown_subprocess()

            elif self._proc is not None:
                # Dead subprocess — clean up
                self._shutdown_subprocess(timeout = 2)

            disable_xet = sub_config.get("disable_xet", False) or (
                os.environ.get("HF_HUB_DISABLE_XET") == "1"
            )

            for attempt in range(2):
                logger.info(
                    "Spawning fresh inference subprocess for '%s' "
                    "(transformers %s.x, attempt %d/2%s)",
                    model_name,
                    needed_major,
                    attempt + 1,
                    ", xet disabled" if disable_xet else "",
                )
                sub_config["disable_xet"] = disable_xet
                self._spawn_subprocess(sub_config)

                try:
                    resp = self._wait_response("loaded")
                except DownloadStallError:
                    # First stall and Xet was enabled -> retry with Xet disabled
                    if attempt == 0 and not disable_xet:
                        logger.warning(
                            "Download stalled for '%s' -- retrying with "
                            "HF_HUB_DISABLE_XET=1",
                            model_name,
                        )
                        self._shutdown_subprocess(timeout = 5)
                        disable_xet = True
                        continue
                    # Second stall (or already had xet disabled) -> give up
                    self._shutdown_subprocess(timeout = 5)
                    raise RuntimeError(
                        f"Download stalled for '{model_name}' even with "
                        f"HF_HUB_DISABLE_XET=1 -- check your network connection"
                    )

                # Got a response — check success
                if resp.get("success"):
                    self._current_transformers_major = needed_major
                    model_info = resp.get("model_info", {})
                    self.active_model_name = model_info.get("identifier", model_name)
                    self.models[self.active_model_name] = {
                        "is_vision": model_info.get("is_vision", False),
                        "is_lora": model_info.get("is_lora", False),
                        "display_name": model_info.get("display_name", model_name),
                        "is_audio": model_info.get("is_audio", False),
                        "audio_type": model_info.get("audio_type"),
                        "has_audio_input": model_info.get("has_audio_input", False),
                    }
                    self.loading_models.discard(model_name)
                    logger.info(
                        "Model '%s' loaded successfully in subprocess", model_name
                    )
                    return True
                else:
                    error = resp.get("error", "Failed to load model")
                    self.loading_models.discard(model_name)
                    self.active_model_name = None
                    self.models.clear()
                    raise Exception(error)

        except Exception:
            self.loading_models.discard(model_name)
            self.active_model_name = None
            self.models.clear()
            raise