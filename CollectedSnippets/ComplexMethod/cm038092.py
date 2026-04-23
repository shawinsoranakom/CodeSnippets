def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        if not mm_data:
            # Avoid warning from HF logger for text-only input
            tokenizer = self.info.get_tokenizer()
            prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
            return BatchFeature(dict(input_ids=[prompt_ids]), tensor_type="pt")

        processed_outputs = super()._call_hf_processor(
            prompt=prompt,
            mm_data=mm_data,
            mm_kwargs=mm_kwargs,
            tok_kwargs=tok_kwargs,
        )
        hf_processor = self.info.get_hf_processor()

        if "videos" in mm_data:
            visual_indicators = [
                hf_processor.construct_visual_indicators((1, 1, 1), True)
                for grid in processed_outputs["video_grids"]
            ]
            indicator_tokens = [
                self.visual_indicators_to_visual_tokens(indicator)
                for indicator in visual_indicators
            ]
            processed_outputs["video_indicator_tokens"] = torch.tensor(indicator_tokens)
        if "images" in mm_data:
            visual_indicators = [
                hf_processor.construct_visual_indicators((1, 1, 1), False)
                for grid in processed_outputs["grids"]
            ]
            indicator_tokens = [
                self.visual_indicators_to_visual_tokens(indicator)
                for indicator in visual_indicators
            ]

            processed_outputs["indicator_tokens"] = torch.tensor(indicator_tokens)
        return processed_outputs