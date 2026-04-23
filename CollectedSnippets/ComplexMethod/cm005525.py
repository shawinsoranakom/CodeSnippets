def _valid_auto_compile_criteria(
        self: "GenerativePreTrainedModel", model_kwargs: dict[str, Any], generation_config: GenerationConfig
    ) -> bool:
        """
        Determines whether to trigger auto-compilation of the model's forward pass at generation time.
        """
        # Override: honor `disable_compile` flag
        if generation_config.disable_compile:
            return False

        cache = model_kwargs.get("past_key_values", model_kwargs.get("cache_params"))

        # Base logic
        valid_hardware = self.device.type in ["cuda", "xpu", "neuron"] or bool(
            generation_config.compile_config is not None and generation_config.compile_config._compile_all_devices
        )
        # Note: for some models that only use linear attention (e.g. Mamba), even a DynamicCache is compileable since all
        # layers are, but we don't want to ALWAYS compile when calling `generate`, so we check the type
        using_compilable_cache = cache is not None and cache.is_compileable and type(cache) is not DynamicCache
        can_compile = valid_hardware and using_compilable_cache

        # Exception 1: Some quantization methods do not support compilation
        if getattr(self, "hf_quantizer", None) is not None:
            can_compile &= self.hf_quantizer.is_compileable

        if hasattr(self, "hf_device_map"):
            all_model_devices = set(self.hf_device_map.values())
            # Exception 2: Don't compile if the model is using CPU offload (as of April 2025, this results in a crash)
            has_cpu_offload = "cpu" in all_model_devices and len(all_model_devices) > 1
            can_compile &= not has_cpu_offload

            # Exception 3: Disk offload is not supported for compilation
            has_disk_offload = "disk" in all_model_devices
            can_compile &= not has_disk_offload

        # If the user has manually specified compilation options, but compilation is not possible, let's warn
        # them
        if generation_config.compile_config is not None and not can_compile:
            logger.warning_once(
                "You have set `compile_config`, but we are unable to meet the criteria for compilation. Compilation "
                "will be skipped."
            )

        if can_compile:
            # Finally: if we can compile, disable tokenizers parallelism
            os.environ["TOKENIZERS_PARALLELISM"] = "0"

            # If we use FA and a static cache, we cannot compile with fullgraph
            if is_flash_attention_requested(self.config):
                # only raise warning if the user passed an explicit compile-config
                if generation_config.compile_config is not None and generation_config.compile_config.fullgraph:
                    logger.warning_once(
                        "When using Flash Attention and a static cache, you cannot use the option `CompileConfig(fullgraph=True)` as "
                        "FA introduces graph breaks. We overrode the option with `fullgraph=False`."
                    )
                    generation_config.compile_config.fullgraph = False

        return can_compile