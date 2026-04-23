def get_mrope_input_positions(
        self,
        input_tokens: list[int],
        mm_features: list[MultiModalFeatureSpec],
    ) -> tuple[torch.Tensor, int]:
        kwargs = MultiModalFeatureSpec.gather_kwargs(
            mm_features,
            {
                "image_grid_thw",
                "video_grid_thw",
                "mm_token_type_ids",
                "second_per_grid_ts",
                "audio_feature_lengths",
                "use_audio_in_video",
            },
        )
        if any(
            v
            for k, v in kwargs.items()
            if k not in {"image_grid_thw", "mm_token_type_ids"}
        ):
            raise NotImplementedError(
                "Transformers modeling backend only supports images."
            )

        image_grid_thw = kwargs.get("image_grid_thw", [])
        video_grid_thw = kwargs.get("video_grid_thw", [])
        mm_token_type_ids = kwargs.get("mm_token_type_ids")

        image_grid_thw = (torch.stack if image_grid_thw else torch.tensor)(
            image_grid_thw
        )
        video_grid_thw = (torch.stack if video_grid_thw else torch.tensor)(
            video_grid_thw
        )

        # In v4 `get_rope_index` doesn't have wildcard `kwargs`, and
        # can't accept arbitrary args, even if its value is `None`
        kwargs = {}
        if not hasattr(self, "_get_rope_index_accepts_mm_token_type_ids"):
            import inspect

            sig = inspect.signature(self.model.get_rope_index)
            params = sig.parameters
            self._get_rope_index_accepts_mm_token_type_ids = (
                "mm_token_type_ids" in params
                or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
            )
        if self._get_rope_index_accepts_mm_token_type_ids:
            if mm_token_type_ids:
                kwargs["mm_token_type_ids"] = torch.cat(mm_token_type_ids)
            else:
                shape = (1, len(input_tokens))
                kwargs["mm_token_type_ids"] = torch.zeros(*shape, dtype=torch.int)

        mrope_positions, mrope_position_delta = self.model.get_rope_index(
            input_ids=torch.tensor(input_tokens).unsqueeze(0),
            image_grid_thw=image_grid_thw,
            video_grid_thw=video_grid_thw,
            **kwargs,
        )

        mrope_positions = mrope_positions[:, 0]
        mrope_position_delta = mrope_position_delta[0].item()

        return mrope_positions, mrope_position_delta