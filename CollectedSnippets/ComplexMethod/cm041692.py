def _compute_rope_position_ids(
        self, features: dict[str, "torch.Tensor"], mm_inputs: dict[str, Any]
    ) -> None:
        r"""Compute position_ids and rope_deltas via get_rope_func for VLMs."""
        rope_index_kwargs = {
            "input_ids": features["input_ids"],
            "image_grid_thw": mm_inputs.get("image_grid_thw"),
            "video_grid_thw": mm_inputs.get("video_grid_thw"),
            "attention_mask": (features["attention_mask"] >= 1).float(),
        }
        if features["attention_mask"].sum() == 0:
            features["position_ids"] = torch.zeros((3, *features["input_ids"].shape))
            features["rope_deltas"] = torch.zeros(features["input_ids"].shape[0])
            return

        if "mm_token_type_ids" in inspect.signature(self.get_rope_func).parameters:
            image_token_id = getattr(self.model.config, "image_token_id", None)
            video_token_id = getattr(self.model.config, "video_token_id", None)
            if image_token_id is not None or video_token_id is not None:
                mm_token_type_ids = torch.zeros_like(features["input_ids"])
                if image_token_id is not None:
                    mm_token_type_ids[features["input_ids"] == image_token_id] = 1
                if video_token_id is not None:
                    mm_token_type_ids[features["input_ids"] == video_token_id] = 2
                rope_index_kwargs["mm_token_type_ids"] = mm_token_type_ids

        if "second_per_grid_ts" in mm_inputs:  # for qwen2vl
            rope_index_kwargs["second_per_grid_ts"] = mm_inputs.get("second_per_grid_ts")
        elif "video_second_per_grid" in mm_inputs:  # for qwen2.5 omni
            rope_index_kwargs["second_per_grids"] = mm_inputs.get("video_second_per_grid")

        if getattr(self.model.config, "model_type", None) in ["qwen2_5_omni_thinker", "qwen3_omni_moe_thinker"]:
            rope_index_kwargs["use_audio_in_video"] = getattr(self.processor, "use_audio_in_video", False)
            feature_attention_mask = mm_inputs.get("feature_attention_mask", None)
            if feature_attention_mask is not None:  # FIXME: need to get video image lengths
                audio_feature_lengths = torch.sum(feature_attention_mask, dim=1)
                rope_index_kwargs["audio_seqlens"] = audio_feature_lengths  # prepare for input

            features["position_ids"], rope_deltas = self.get_rope_func(**rope_index_kwargs)
            features["rope_deltas"] = rope_deltas - (1 - rope_index_kwargs["attention_mask"]).sum(
                dim=-1
            ).unsqueeze(-1)
        else:  # for qwen vl
            features["position_ids"], features["rope_deltas"] = self.get_rope_func(**rope_index_kwargs)