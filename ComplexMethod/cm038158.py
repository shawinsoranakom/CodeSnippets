def embed_multimodal(
        self, **kwargs
    ) -> list[torch.Tensor] | torch.Tensor | tuple[torch.Tensor, ...] | None:
        """Transform audio waveforms -> initial whisper post-conv embeddings"""
        audio_inputs = self._parse_and_validate_audio_arrays(**kwargs)

        if audio_inputs is None:
            logger.warning(
                "Realtime model received no audio inputs in "
                "embed_multimodal. Returning empty embeddings."
            )
            return []

        def _truncate_left(
            sample: torch.Tensor, mult_of: int, pos: int
        ) -> torch.Tensor:
            assert pos in [0, 1], pos
            if (ctx := sample.shape[pos] % mult_of) != 0:
                sample = sample[ctx:] if pos == 0 else sample[:, ctx:]
                assert sample.shape[pos] > 0, (
                    f"Sample is empty after truncation with ctx {ctx}"
                )

            return sample

        mel_features = [
            self.whisper_encoder.compute_whisper_melspec(audio).to(
                self.whisper_encoder.dtype
            )
            for audio in audio_inputs
        ]

        # we truncate the left most mel feature
        # if the sequence length in impair
        mel_features = [_truncate_left(mel, 2, 1) for mel in mel_features]

        seq_lens = [mel.shape[1] for mel in mel_features]
        # [total_num_20ms_frames, hidden_size]
        audio_embeddings = self.whisper_encoder.whisper_encoder.forward_conv(
            mel_features
        )
        conv_stride = self.whisper_encoder.whisper_encoder.total_stride
        audio_embeddings_per_sample = audio_embeddings.split(
            [s // conv_stride for s in seq_lens], dim=0
        )

        # audio_embeddings per sample need to be divisible by 4
        pool_size = self.config.audio_config.block_pool_size

        audio_embeddings_per_sample = [
            _truncate_left(sample, pool_size, 0)
            for sample in audio_embeddings_per_sample
        ]

        audio_embeddings_per_sample = [
            e.view(e.shape[0] // pool_size, e.shape[1] * pool_size)
            for e in audio_embeddings_per_sample
        ]
        return audio_embeddings_per_sample