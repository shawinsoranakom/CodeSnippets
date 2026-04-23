def adjust_generation_fn(
        self: "GenerativePreTrainedModel",
        generation_config,
        from_auto_class,
        from_pipeline,
        pretrained_model_name_or_path,
        cache_dir,
        force_download,
        proxies,
        local_files_only,
        token,
        revision,
        subfolder,
        trust_remote_code,
        **kwargs,
    ):
        if self.can_generate() and generation_config is not None:
            self.generation_config = self.generation_config.from_dict(generation_config.to_dict())
        elif self.can_generate() and pretrained_model_name_or_path is not None:
            repo_loading_kwargs = {
                "cache_dir": cache_dir,
                "force_download": force_download,
                "proxies": proxies,
                "local_files_only": local_files_only,
                "token": token,
                "revision": revision,
                "subfolder": subfolder,
                **kwargs,
            }
            # Load generation config
            try:
                self.generation_config = GenerationConfig.from_pretrained(
                    pretrained_model_name_or_path,
                    _from_auto=from_auto_class,
                    _from_pipeline=from_pipeline,
                    **repo_loading_kwargs,
                )
            except OSError:
                # `self` already has a generation config created from model config, but model config will
                # not contain any generation-specific params. These are popped at config's `__init__`.
                # Thus we have to load from `config.json` and create a generation config from it (for BART)
                logger.info(
                    "Generation config file not found, using a generation config created from the model config."
                )
                self.generation_config = GenerationConfig.from_pretrained(
                    pretrained_model_name_or_path,
                    config_file_name="config.json",
                    _from_auto=from_auto_class,
                    _from_pipeline=from_pipeline,
                    _from_model_config=True,
                    **repo_loading_kwargs,
                )

            # Load custom generate function if `pretrained_model_name_or_path` defines it (and override `generate`)
            if hasattr(self, "load_custom_generate") and trust_remote_code:
                try:
                    custom_generate = self.load_custom_generate(
                        pretrained_model_name_or_path, trust_remote_code=trust_remote_code, **repo_loading_kwargs
                    )
                    self.generate = functools.partial(custom_generate, model=self)
                except OSError:  # there is no custom generate function
                    pass