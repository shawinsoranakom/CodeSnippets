def validate_architecture(self):
        """Part of `@strict`-powered validation. Validates the architecture of the config."""
        if self.positionwise_conv_kernel_size % 2 == 0:
            raise ValueError(
                f"positionwise_conv_kernel_size must be odd, but got {self.self.positionwise_conv_kernel_size} instead."
            )
        if self.encoder_kernel_size % 2 == 0:
            raise ValueError(f"encoder_kernel_size must be odd, but got {self.encoder_kernel_size} instead.")
        if self.decoder_kernel_size % 2 == 0:
            raise ValueError(f"decoder_kernel_size must be odd, but got {self.decoder_kernel_size} instead.")
        if self.duration_predictor_kernel_size % 2 == 0:
            raise ValueError(
                f"duration_predictor_kernel_size must be odd, but got {self.duration_predictor_kernel_size} instead."
            )
        if self.energy_predictor_kernel_size % 2 == 0:
            raise ValueError(
                f"energy_predictor_kernel_size must be odd, but got {self.energy_predictor_kernel_size} instead."
            )
        if self.energy_embed_kernel_size % 2 == 0:
            raise ValueError(f"energy_embed_kernel_size must be odd, but got {self.energy_embed_kernel_size} instead.")
        if self.pitch_predictor_kernel_size % 2 == 0:
            raise ValueError(
                f"pitch_predictor_kernel_size must be odd, but got {self.pitch_predictor_kernel_size} instead."
            )
        if self.pitch_embed_kernel_size % 2 == 0:
            raise ValueError(f"pitch_embed_kernel_size must be odd, but got {self.pitch_embed_kernel_size} instead.")
        if self.hidden_size % self.encoder_num_attention_heads != 0:
            raise ValueError("The hidden_size must be evenly divisible by encoder_num_attention_heads.")
        if self.hidden_size % self.decoder_num_attention_heads != 0:
            raise ValueError("The hidden_size must be evenly divisible by decoder_num_attention_heads.")
        if self.use_masking and self.use_weighted_masking:
            raise ValueError("Either use_masking or use_weighted_masking can be True, but not both.")