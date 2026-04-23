def _call_hf_processor(
        self,
        prompt: str,
        mm_data: dict[str, object],
        mm_kwargs: Mapping[str, Any],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        # Normalize input: handle deprecated key and list conversion.
        if "audios" in mm_data:
            mm_data["audio"] = mm_data.pop("audios")

        audio = mm_data.get("audio", [])
        audio_list = [audio] if audio and not isinstance(audio, list) else audio

        # Early return for text-only.
        if not audio_list:
            prompt_ids = self.info.get_tokenizer().encode(prompt)
            prompt_ids = self._apply_hf_processor_tokens_only(prompt_ids)
            return BatchFeature(dict(input_ids=[prompt_ids]), tensor_type="pt")

        # Handle sampling_rate
        feature_extractor = self.info.get_feature_extractor(**mm_kwargs)
        mm_kwargs = dict(
            **mm_kwargs,
            sampling_rate=feature_extractor.sampling_rate,
        )

        # Call parent method
        outputs = super()._call_hf_processor(
            prompt=prompt,
            mm_data=mm_data,
            mm_kwargs=mm_kwargs,
            tok_kwargs=tok_kwargs,
        )

        # Postprocess: rename mask and add chunk counts
        # Handle different key names from different transformers versions
        if "input_features_mask" in outputs:
            outputs["feature_attention_mask"] = outputs.pop("input_features_mask")
        elif "input_features_mask" not in outputs and "input_features" in outputs:
            # If no mask is provided, create one from input_features
            input_features = outputs["input_features"]
            if isinstance(input_features, torch.Tensor):
                # Create a mask of all ones matching the sequence length
                mask = torch.ones(
                    input_features.shape[0],
                    input_features.shape[-1],
                    dtype=torch.long,
                )
                outputs["feature_attention_mask"] = mask

        # Get processor for chunk counts calculation
        processor = self.info.get_hf_processor(**mm_kwargs)

        # Override chunk counts calculation with GLM-ASR specific logic
        chunk_counts = self._calculate_chunk_counts(
            audio_list, processor.feature_extractor, processor
        )
        outputs["chunk_counts"] = torch.tensor(chunk_counts, dtype=torch.long)

        return outputs