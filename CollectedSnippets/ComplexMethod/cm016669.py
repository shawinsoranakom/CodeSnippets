def _build_guide_self_attention_mask(self, x, transformer_options, merged_args):
        """Build self-attention mask for per-guide attention attenuation.

        Reads resolved_guide_entries from merged_args (computed in _process_input)
        to build a log-space additive bias mask that attenuates noisy ↔ guide
        attention for each guide reference independently.

        Returns None if no attenuation is needed (all strengths == 1.0 and no
        spatial masks, or no guide tokens).
        """
        if isinstance(x, list):
            # AV model: x = [vx, ax]; use vx for token count and device
            total_tokens = x[0].shape[1]
            device = x[0].device
            dtype = x[0].dtype
        else:
            total_tokens = x.shape[1]
            device = x.device
            dtype = x.dtype

        num_guide_tokens = merged_args.get("num_guide_tokens", 0)
        if num_guide_tokens == 0:
            return None

        resolved_entries = merged_args.get("resolved_guide_entries", None)
        if not resolved_entries:
            return None

        # Check if any attenuation is actually needed
        needs_attenuation = any(
            e["strength"] < 1.0 or e.get("pixel_mask") is not None
            for e in resolved_entries
        )
        if not needs_attenuation:
            return None

        # Build per-guide-token weights for all tracked guide tokens.
        # Guides are appended in order at the end of the sequence.
        guide_start = total_tokens - num_guide_tokens
        all_weights = []
        total_tracked = 0

        for entry in resolved_entries:
            surviving = entry["surviving_count"]
            if surviving == 0:
                continue

            strength = entry["strength"]
            pixel_mask = entry.get("pixel_mask")
            latent_shape = entry.get("latent_shape")

            if pixel_mask is not None and latent_shape is not None:
                f_lat, h_lat, w_lat = latent_shape
                per_token = self._downsample_mask_to_latent(
                    pixel_mask.to(device=device, dtype=dtype),
                    f_lat, h_lat, w_lat,
                )
                # per_token shape: (B, f_lat*h_lat*w_lat).
                # Collapse batch dim — the mask is assumed identical across the
                # batch; validate and take the first element to get (1, tokens).
                if per_token.shape[0] > 1:
                    ref = per_token[0]
                    for bi in range(1, per_token.shape[0]):
                        if not torch.equal(ref, per_token[bi]):
                            logger.warning(
                                "pixel_mask differs across batch elements; "
                                "using first element only."
                            )
                            break
                    per_token = per_token[:1]
                # `surviving` is the post-grid_mask token count.
                # Clamp to surviving to handle any mismatch safely.
                n_weights = min(per_token.shape[1], surviving)
                weights = per_token[:, :n_weights] * strength  # (1, n_weights)
            else:
                weights = torch.full(
                    (1, surviving), strength, device=device, dtype=dtype
                )

            all_weights.append(weights)
            total_tracked += weights.shape[1]

        if not all_weights:
            return None

        # Concatenate per-token weights for all tracked guides
        tracked_weights = torch.cat(all_weights, dim=1)  # (1, total_tracked)

        # Check if any weight is actually < 1.0 (otherwise no attenuation needed)
        if (tracked_weights >= 1.0).all():
            return None

        # Build the mask: guide tokens are at the end of the sequence.
        # Tracked guides come first (in order), untracked follow.
        return self._build_self_attention_mask(
            total_tokens, num_guide_tokens, total_tracked,
            tracked_weights, guide_start, device, dtype,
        )