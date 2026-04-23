def append_keyframe(cls, positive, negative, frame_idx, latent_image, noise_mask, guiding_latent, strength, scale_factors, guide_mask=None, in_channels=128, latent_downscale_factor=1, causal_fix=None):
        if latent_image.shape[1] != in_channels or guiding_latent.shape[1] != in_channels:
            raise ValueError("Adding guide to a combined AV latent is not supported.")

        positive = cls.add_keyframe_index(positive, frame_idx, guiding_latent, scale_factors, latent_downscale_factor, causal_fix=causal_fix)
        negative = cls.add_keyframe_index(negative, frame_idx, guiding_latent, scale_factors, latent_downscale_factor, causal_fix=causal_fix)

        if guide_mask is not None:
            target_h = max(noise_mask.shape[3], guide_mask.shape[3])
            target_w = max(noise_mask.shape[4], guide_mask.shape[4])

            if noise_mask.shape[3] == 1 or noise_mask.shape[4] == 1:
                noise_mask = noise_mask.expand(-1, -1, -1, target_h, target_w)

            if guide_mask.shape[3] == 1 or guide_mask.shape[4] == 1:
                guide_mask = guide_mask.expand(-1, -1, -1, target_h, target_w)
            mask = guide_mask - strength
        else:
            mask = torch.full(
                (noise_mask.shape[0], 1, guiding_latent.shape[2], noise_mask.shape[3], noise_mask.shape[4]),
                1.0 - strength,
                dtype=noise_mask.dtype,
                device=noise_mask.device,
            )
        # This solves audio video combined latent case where latent_image has audio latent concatenated
        # in channel dimension with video latent. The solution is to pad guiding latent accordingly.
        if latent_image.shape[1] > guiding_latent.shape[1]:
            pad_len = latent_image.shape[1] - guiding_latent.shape[1]
            guiding_latent = torch.nn.functional.pad(guiding_latent, pad=(0, 0, 0, 0, 0, 0, 0, pad_len), value=0)
        latent_image = torch.cat([latent_image, guiding_latent], dim=2)
        noise_mask = torch.cat([noise_mask, mask], dim=2)
        return positive, negative, latent_image, noise_mask