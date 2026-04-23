def _set_default_chunked_prefill_and_prefix_caching_args(
        self, model_config: ModelConfig
    ) -> None:
        default_chunked_prefill = model_config.is_chunked_prefill_supported
        default_prefix_caching = model_config.is_prefix_caching_supported

        if self.enable_chunked_prefill is None:
            self.enable_chunked_prefill = default_chunked_prefill

            logger.debug(
                "%s chunked prefill by default",
                "Enabling" if default_chunked_prefill else "Disabling",
            )
        elif (
            model_config.runner_type == "generate"
            and not self.enable_chunked_prefill
            and default_chunked_prefill
        ):
            logger.warning_once(
                "This model does not officially support disabling chunked prefill. "
                "Disabling this manually may cause the engine to crash "
                "or produce incorrect outputs.",
            )
        elif (
            model_config.runner_type == "pooling"
            and self.enable_chunked_prefill
            and not default_chunked_prefill
        ):
            logger.warning_once(
                "This model does not officially support chunked prefill. "
                "Enabling this manually may cause the engine to crash "
                "or produce incorrect outputs.",
            )

        if self.enable_prefix_caching is None:
            self.enable_prefix_caching = default_prefix_caching

            logger.debug(
                "%s prefix caching by default",
                "Enabling" if default_prefix_caching else "Disabling",
            )
        elif (
            model_config.runner_type == "pooling"
            and self.enable_prefix_caching
            and not default_prefix_caching
        ):
            logger.warning_once(
                "This model does not officially support prefix caching. "
                "Enabling this manually may cause the engine to crash "
                "or produce incorrect outputs.",
            )

        # Disable chunked prefill and prefix caching for:
        # RISCV CPUs in V1
        if current_platform.is_cpu() and current_platform.get_cpu_architecture() in (
            CpuArchEnum.RISCV,
        ):
            logger.info(
                "Chunked prefill is not supported for"
                "RISC-V CPUs; "
                "disabling it for V1 backend."
            )
            self.enable_chunked_prefill = False
            logger.info(
                "Prefix caching is not supported for "
                "RISC-V CPUs; "
                "disabling it for V1 backend."
            )
            self.enable_prefix_caching = False