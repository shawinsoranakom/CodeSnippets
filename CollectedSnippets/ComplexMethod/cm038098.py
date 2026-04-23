def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        mm_data = dict(mm_data)
        audios = mm_data.pop("audios", [])

        def pad_to_hop_length(x: np.ndarray, hop_length: int) -> np.ndarray:
            length = x.shape[-1]
            if length % hop_length != 0:
                pad_length = hop_length - (length % hop_length)
                x = np.pad(x, (0, pad_length), mode="constant", constant_values=0)
            return x

        # NOTE: WhisperFeatureExtractor cannot handle empty list of audios
        feature_extractor = self.info.get_feature_extractor(**mm_kwargs)
        hop_length = feature_extractor.hop_length
        if audios:
            # NOTE: Qwen3-Omni processor accept "audio"
            # To make sure the cache works with padding=True, we pre-padded
            # the audio to multiple of hop_length.
            mm_data["audio"] = [
                pad_to_hop_length(audio, hop_length)
                if isinstance(audio, np.ndarray)
                else (pad_to_hop_length(audio[0], hop_length), audio[1])
                for audio in audios
            ]

            # TODO(Isotr0py): Remove this patch after upstream fix PR
            # released and Transformers version update:
            # https://github.com/huggingface/transformers/pull/41473
            mm_kwargs = dict(mm_kwargs)
            tok_kwargs = dict(tok_kwargs)
            mm_kwargs["audio_kwargs"] = dict(mm_kwargs.get("audio_kwargs") or {})
            mm_kwargs["text_kwargs"] = dict(mm_kwargs.get("text_kwargs") or {})
            if Version(TRANSFORMERS_VERSION) < Version("4.58.0"):
                # Extract audio_sample_rate before restructuring
                audio_sample_rate = mm_kwargs.pop("audio_sample_rate", None)

                # move truncation to audio_kwargs level to avoid conflict
                # with tok_kwargs
                mm_kwargs["audio_kwargs"].setdefault(
                    "truncation", mm_kwargs.pop("truncation", False)
                )
                mm_kwargs["text_kwargs"].setdefault(
                    "truncation", tok_kwargs.pop("truncation", False)
                )

                # Validate and conditionally pass audio_sample_rate
                # WhisperFeatureExtractor has a fixed sampling rate, and vLLM's
                # audio loader already resamples audio to the target rate.
                # Only pass the value if it matches to avoid unexpected behavior.
                if audio_sample_rate is not None:
                    expected_sr = feature_extractor.sampling_rate
                    if audio_sample_rate != expected_sr:
                        logger.warning(
                            "[%s] audio_sample_rate mismatch: user provided %dHz "
                            "but model expects %dHz. Ignoring user value. "
                            "vLLM's audio loader already resampled to %dHz.",
                            self.__class__.__name__,
                            audio_sample_rate,
                            expected_sr,
                            expected_sr,
                        )
                    else:
                        # Sample rate matches, safe to pass
                        mm_kwargs["audio_kwargs"]["audio_sample_rate"] = (
                            audio_sample_rate
                        )

        hf_inputs = super()._call_hf_processor(
            prompt=prompt,
            mm_data=mm_data,
            mm_kwargs=mm_kwargs,
            tok_kwargs=tok_kwargs,
        )

        if (
            "audio_feature_lengths" in hf_inputs
            and "feature_attention_mask" in hf_inputs
            and (audios := mm_data.get("audio", []))
        ):
            audio_num_frames = []
            for _, audio in enumerate(audios):
                audio_length = len(audio[0]) if isinstance(audio, tuple) else len(audio)
                num_frame = (
                    (audio_length // hop_length)
                    if audio_length % hop_length == 0
                    else (audio_length // hop_length - 1)
                )
                if mm_kwargs.get("truncation", False):
                    num_frame = min(
                        num_frame, feature_extractor.n_samples // hop_length
                    )
                audio_num_frames.append(num_frame)
            hf_inputs["feature_attention_mask"] = [
                torch.ones(num_frame) for num_frame in audio_num_frames
            ]
            hf_inputs["audio_feature_lengths"] = torch.tensor(audio_num_frames)
        return hf_inputs