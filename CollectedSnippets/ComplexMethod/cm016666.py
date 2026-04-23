def _prepare_timestep(self, timestep, batch_size, hidden_dtype, **kwargs):
        """Prepare timestep embeddings."""
        # TODO: some code reuse is needed here.
        grid_mask = kwargs.get("grid_mask", None)
        if grid_mask is not None:
            timestep = timestep[:, grid_mask]

        timestep_scaled = timestep * self.timestep_scale_multiplier

        v_timestep, v_embedded_timestep = self.adaln_single(
            timestep_scaled.flatten(),
            {"resolution": None, "aspect_ratio": None},
            batch_size=batch_size,
            hidden_dtype=hidden_dtype,
        )

        # Calculate patches_per_frame from orig_shape: [batch, channels, frames, height, width]
        # Video tokens are arranged as (frames * height * width), so patches_per_frame = height * width
        orig_shape = kwargs.get("orig_shape")
        has_spatial_mask = kwargs.get("has_spatial_mask", None)
        v_patches_per_frame = None
        if not has_spatial_mask and orig_shape is not None and len(orig_shape) == 5:
            # orig_shape[3] = height, orig_shape[4] = width (in latent space)
            v_patches_per_frame = orig_shape[3] * orig_shape[4]

        # Reshape to [batch_size, num_tokens, dim] and compress for storage
        v_timestep = CompressedTimestep(v_timestep.view(batch_size, -1, v_timestep.shape[-1]), v_patches_per_frame)
        v_embedded_timestep = CompressedTimestep(v_embedded_timestep.view(batch_size, -1, v_embedded_timestep.shape[-1]), v_patches_per_frame)

        v_prompt_timestep = compute_prompt_timestep(
            self.prompt_adaln_single, timestep_scaled, batch_size, hidden_dtype
        )

        # Prepare audio timestep
        a_timestep = kwargs.get("a_timestep")
        ref_audio_seq_len = kwargs.get("ref_audio_seq_len", 0)
        if ref_audio_seq_len > 0 and a_timestep is not None:
            # Reference tokens must have timestep=0, expand scalar/1D timestep to per-token so ref=0 and target=sigma.
            target_len = kwargs.get("target_audio_seq_len")
            if a_timestep.dim() <= 1:
                a_timestep = a_timestep.view(-1, 1).expand(batch_size, target_len)
            ref_ts = torch.zeros(batch_size, ref_audio_seq_len, *a_timestep.shape[2:], device=a_timestep.device, dtype=a_timestep.dtype)
            a_timestep = torch.cat([ref_ts, a_timestep], dim=1)
        if a_timestep is not None:
            a_timestep_scaled = a_timestep * self.timestep_scale_multiplier
            a_timestep_flat = a_timestep_scaled.flatten()
            timestep_flat = timestep_scaled.flatten()
            av_ca_factor = self.av_ca_timestep_scale_multiplier / self.timestep_scale_multiplier

            # Cross-attention timesteps - compress these too
            av_ca_audio_scale_shift_timestep, _ = self.av_ca_audio_scale_shift_adaln_single(
                timestep.max().expand_as(a_timestep_flat),
                {"resolution": None, "aspect_ratio": None},
                batch_size=batch_size,
                hidden_dtype=hidden_dtype,
            )
            av_ca_video_scale_shift_timestep, _ = self.av_ca_video_scale_shift_adaln_single(
                a_timestep.max().expand_as(timestep_flat),
                {"resolution": None, "aspect_ratio": None},
                batch_size=batch_size,
                hidden_dtype=hidden_dtype,
            )
            av_ca_a2v_gate_noise_timestep, _ = self.av_ca_a2v_gate_adaln_single(
                a_timestep.max().expand_as(timestep_flat) * av_ca_factor,
                {"resolution": None, "aspect_ratio": None},
                batch_size=batch_size,
                hidden_dtype=hidden_dtype,
            )
            av_ca_v2a_gate_noise_timestep, _ = self.av_ca_v2a_gate_adaln_single(
                timestep.max().expand_as(a_timestep_flat) * av_ca_factor,
                {"resolution": None, "aspect_ratio": None},
                batch_size=batch_size,
                hidden_dtype=hidden_dtype,
            )

            # Compress cross-attention timesteps (only video side, audio is too small to benefit)
            # v_patches_per_frame is None for spatial masks, set for temporal masks or no mask
            cross_av_timestep_ss = [
                av_ca_audio_scale_shift_timestep.view(batch_size, -1, av_ca_audio_scale_shift_timestep.shape[-1]),
                CompressedTimestep(av_ca_video_scale_shift_timestep.view(batch_size, -1, av_ca_video_scale_shift_timestep.shape[-1]), v_patches_per_frame),  # video - compressed if possible
                CompressedTimestep(av_ca_a2v_gate_noise_timestep.view(batch_size, -1, av_ca_a2v_gate_noise_timestep.shape[-1]), v_patches_per_frame),  # video - compressed if possible
                av_ca_v2a_gate_noise_timestep.view(batch_size, -1, av_ca_v2a_gate_noise_timestep.shape[-1]),
            ]

            a_timestep, a_embedded_timestep = self.audio_adaln_single(
                a_timestep_flat,
                {"resolution": None, "aspect_ratio": None},
                batch_size=batch_size,
                hidden_dtype=hidden_dtype,
            )
            # Audio timesteps
            a_timestep = a_timestep.view(batch_size, -1, a_timestep.shape[-1])
            a_embedded_timestep = a_embedded_timestep.view(batch_size, -1, a_embedded_timestep.shape[-1])

            a_prompt_timestep = compute_prompt_timestep(
                self.audio_prompt_adaln_single, a_timestep_scaled, batch_size, hidden_dtype
            )
        else:
            a_timestep = timestep_scaled
            a_embedded_timestep = kwargs.get("embedded_timestep")
            cross_av_timestep_ss = []
            a_prompt_timestep = None

        return [v_timestep, a_timestep, cross_av_timestep_ss, v_prompt_timestep, a_prompt_timestep], [
            v_embedded_timestep,
            a_embedded_timestep,
        ], None