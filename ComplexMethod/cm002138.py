def check_validity(self, skip_validity_check: bool = False) -> None:
        if skip_validity_check:
            return
        # If flash_attention_2 is selected but not available, default to SDPA
        if self.attn_implementation == "flash_attention_2" and not is_fa2_or_kernel_available():
            logger.error("Flash attention is not available. Defaulting to SDPA.")
            self.attn_implementation = "sdpa"

        # The combination of flash_attention_2, compile and generate is not supported # FIXME: support it
        if (
            not self.continuous_batching
            and self.attn_implementation == "flash_attention_2"
            and self.compile_config is not None
        ):
            logger.error(
                "The combination of flash_attention_2, compile and generate is not supported. Turning off compile."
            )
            self.compile_config = None

        # Continuous batching does not support flex attention as an attention implementation # FIXME: support it
        if self.attn_implementation == "flex_attention" and self.continuous_batching:
            logger.error(
                "Disabling continuous batching because of invalid configuration: flex attention is not supported."
            )
            self.continuous_batching = False

        # Continuous batching supports compile mode "default" or "max-autotune-no-cudagraphs"
        if (
            self.continuous_batching
            and self.compile_config is not None
            and self.compile_config.mode not in ["default", "max-autotune-no-cudagraphs"]
        ):
            logger.error(
                f"You have continuous batching and compile enabled, but {self.compile_config.mode = } is not supported."
                " Supported modes are: default, max-autotune-no-cudagraphs. Changing to default."
            )
            self.compile_config.mode = "default"