def _align_video_hidden_state(
        self,
        video_hidden_state: torch.Tensor,
        audio_hidden_state: torch.Tensor,
        padding_mask_videos: torch.Tensor | None = None,
        padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Align video_hidden_state to audio_hidden_state by nearest neighbor interpolation.
        """
        if video_hidden_state.shape[1] == audio_hidden_state.shape[1]:
            return video_hidden_state

        if padding_mask_videos is not None:
            video_lengths = padding_mask_videos.sum(dim=-1)
        else:
            video_lengths = video_hidden_state.shape[1] * video_hidden_state.new_ones(
                video_hidden_state.shape[0], dtype=torch.long
            )

        if padding_mask is not None:
            audio_lengths = padding_mask.sum(dim=-1)
        else:
            audio_lengths = audio_hidden_state.shape[1] * audio_hidden_state.new_ones(
                audio_hidden_state.shape[0], dtype=torch.long
            )

        if (audio_lengths == video_hidden_state.shape[1]).all() or (
            video_lengths == audio_hidden_state.shape[1]
        ).all():
            # no need to align taking into account the padding masks
            # note: when one of the above is true, we can expect the other to be true as there is no reason
            # to have masked audio without masked video and vice versa

            return nn.functional.interpolate(
                video_hidden_state.transpose(1, 2), size=audio_hidden_state.shape[1], mode="nearest"
            ).transpose(1, 2)

        aligned_shape = (*audio_hidden_state.shape[:2], video_hidden_state.shape[-1])
        aligned_hidden_state = audio_hidden_state.new_zeros(aligned_shape)

        for i, (hidden_state, video_length, audio_length) in enumerate(
            zip(video_hidden_state, video_lengths, audio_lengths)
        ):
            hidden_state = hidden_state[:video_length]
            if hidden_state.numel() > 0 and audio_length > 0:
                interpolated_hidden_state = nn.functional.interpolate(
                    hidden_state[None].transpose(1, 2), size=audio_length, mode="nearest"
                ).transpose(1, 2)[0]
                aligned_hidden_state[i, :audio_length, :] = interpolated_hidden_state

        return aligned_hidden_state