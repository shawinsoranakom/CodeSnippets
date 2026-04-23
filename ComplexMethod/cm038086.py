def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        mm_data = dict(mm_data)
        audios = mm_data.pop("audios", [])

        # NOTE: WhisperFeatureExtractor cannot handle empty list of audios
        if audios:
            # NOTE: Qwen2.5-Omni processor accept "audio"
            mm_data["audio"] = audios
            mm_kwargs = dict(
                **mm_kwargs,
            )

        hf_inputs = super()._call_hf_processor(
            prompt=prompt,
            mm_data=mm_data,
            mm_kwargs=mm_kwargs,
            tok_kwargs=tok_kwargs,
        )

        input_features = hf_inputs.pop("input_features", None)
        feature_attention_mask = hf_inputs.get("feature_attention_mask", None)
        if "input_audio_features" not in hf_inputs and input_features is not None:
            if feature_attention_mask is not None:
                input_features = input_features.permute(0, 2, 1)[
                    feature_attention_mask.bool()
                ].permute(1, 0)
            hf_inputs["input_audio_features"] = input_features
        if (
            "audio_feature_lengths" not in hf_inputs
            and feature_attention_mask is not None
        ):
            hf_inputs["audio_feature_lengths"] = feature_attention_mask.sum(-1)

        video_second_per_grid = hf_inputs.get("video_second_per_grid", None)
        if video_second_per_grid is not None:
            hf_inputs["second_per_grid_ts"] = video_second_per_grid

        use_audio_in_video = mm_kwargs.get("use_audio_in_video", False)
        hf_inputs["use_audio_in_video"] = torch.tensor(use_audio_in_video)

        return hf_inputs