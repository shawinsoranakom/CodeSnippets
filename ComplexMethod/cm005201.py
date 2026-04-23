def forward(
        self, audio_mel: torch.Tensor, audio_mel_mask: torch.BoolTensor, **kwargs: Unpack[TransformersKwargs]
    ) -> tuple | Gemma3nAudioEncoderModelOutput:
        """Encodes a batch of MELs.

        Args:
            audio_mel: a torch.Tensor of shape [batch, num_frames, num_channels,
              mel_bins].

        Returns:
            audio_encodings: a torch.Tensor of shape
                `[batch_size, self.config.audio_soft_tokens_per_image,
                self.config.audio_config.hidden_size]`
            audio_mel_mask: a torch.BoolTensor of shape [batch, num_frames].
        """
        audio_encodings = self.subsample_conv_projection(audio_mel)  # audio_encodings: [B, T_sub, D]

        # Subsample the input audio_mel_mask to match the time dimension of audio_encodings (T_sub)
        t_sub = audio_encodings.shape[1]

        time_stride_product = 1
        for stride_pair_idx in range(len(self.config.sscp_conv_stride_size)):
            time_stride_product *= self.config.sscp_conv_stride_size[stride_pair_idx][0]

        # Create indices for gathering from the original mask.
        # These indices map to original time steps corresponding to the start of each
        # receptive field in the subsampled output.
        indices = torch.arange(t_sub, device=audio_mel_mask.device) * time_stride_product
        indices = torch.clamp(indices, max=audio_mel_mask.shape[1] - 1)  # Ensure indices are valid

        # Expand indices for batch compatibility if B > 1 and indices is 1D.
        if audio_mel_mask.ndim > 1 and indices.ndim == 1:
            indices = indices.unsqueeze(0).expand(audio_mel_mask.shape[0], -1)  # [B, T_sub]
        elif (
            audio_mel_mask.ndim == indices.ndim
            and audio_mel_mask.shape[0] == 1
            and indices.shape[0] != 1
            and t_sub == indices.shape[0]
        ):
            # Handle case where B=1 but indices became [T_sub] instead of [1, T_sub]
            indices = indices.unsqueeze(0)

        current_mask = torch.gather(audio_mel_mask, 1, indices)  # [B, T_sub]

        for block in self.conformer:
            audio_encodings = block(audio_encodings, current_mask)  # Pass the processed mask

        if self.config.conf_reduction_factor > 1:
            audio_encodings = audio_encodings[:, :: self.config.conf_reduction_factor]
            # Reduce the mask as well
            current_mask = current_mask[:, :: self.config.conf_reduction_factor]

        audio_encodings = audio_encodings.masked_fill(current_mask.unsqueeze(-1), 0.0)
        return Gemma3nAudioEncoderModelOutput(
            last_hidden_state=audio_encodings,
            audio_mel_mask=current_mask,
        )