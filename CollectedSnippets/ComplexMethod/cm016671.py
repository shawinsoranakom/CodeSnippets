def forward(self, latent_features, target_shape=None):
        """
        Decode latent features back to audio spectrograms.

        Args:
            latent_features: Encoded latent representation of shape (batch, channels, height, width)
            target_shape: Optional target output shape (batch, channels, time, frequency)
                         If provided, output will be cropped/padded to match this shape

        Returns:
            Reconstructed audio spectrogram of shape (batch, channels, time, frequency)
        """
        assert target_shape is not None, "Target shape is required for CausalAudioAutoencoder Decoder"

        # Transform latent features to decoder's internal feature dimension
        hidden_features = self.conv_in(latent_features)

        # Middle processing
        hidden_features = self.mid.block_1(hidden_features, temb=None)
        hidden_features = self.mid.attn_1(hidden_features)
        hidden_features = self.mid.block_2(hidden_features, temb=None)

        # Upsampling
        # Progressively increase spatial resolution from lowest to highest
        for resolution_level in reversed(range(self.num_resolutions)):
            # Apply residual blocks at current resolution level
            for block_index in range(self.num_res_blocks + 1):
                hidden_features = self.up[resolution_level].block[block_index](hidden_features, temb=None)

                if len(self.up[resolution_level].attn) > 0:
                    hidden_features = self.up[resolution_level].attn[block_index](hidden_features)

            if resolution_level != 0:
                hidden_features = self.up[resolution_level].upsample(hidden_features)

        # Output
        if self.give_pre_end:
            # Return intermediate features before final processing (for debugging/analysis)
            decoded_output = hidden_features
        else:
            # Standard output path: normalize, activate, and convert to output channels
            # Final normalization layer
            hidden_features = self.norm_out(hidden_features)

            # Apply SiLU (Swish) activation function
            hidden_features = self.non_linearity(hidden_features)

            # Final convolution to map to output channels (typically 2 for stereo audio)
            decoded_output = self.conv_out(hidden_features)

            # Optional tanh activation to bound output values to [-1, 1] range
            if self.tanh_out:
                decoded_output = torch.tanh(decoded_output)

        # Adjust shape for audio data
        if target_shape is not None:
            decoded_output = self._adjust_output_shape(decoded_output, target_shape)

        return decoded_output