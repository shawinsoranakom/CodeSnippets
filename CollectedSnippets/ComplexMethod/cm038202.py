def _normalize_audio_feature_inputs(
        self, audio_input: AudioFlamingo3FeatureInputs
    ) -> tuple[torch.Tensor, torch.Tensor, list[int]]:
        input_features = audio_input["input_features"]
        feature_attention_mask = audio_input["feature_attention_mask"]
        chunk_counts = audio_input.get("chunk_counts")

        if isinstance(input_features, list):
            input_features = torch.cat(input_features, dim=0)
            feature_attention_mask = torch.cat(feature_attention_mask, dim=0)

        if chunk_counts is None:
            chunk_counts = [1] * input_features.shape[0]
        elif isinstance(chunk_counts, torch.Tensor):
            chunk_counts = chunk_counts.tolist()
        elif (
            isinstance(chunk_counts, list)
            and chunk_counts
            and isinstance(chunk_counts[0], torch.Tensor)
        ):
            chunk_counts = [count.item() for count in chunk_counts]

        return input_features, feature_attention_mask, chunk_counts