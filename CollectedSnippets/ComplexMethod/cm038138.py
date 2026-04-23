def _parse_and_validate_multimodal_inputs(self, **kwargs: object) -> dict:
        modalities = {}
        # Preserve the order of modalities if there are multiple of them
        # from the order of kwargs.
        for input_key in kwargs:
            if (
                input_key in ("pixel_values_flat", "image_embeds")
                and "images" not in modalities
            ):
                modalities["images"] = self._parse_and_validate_image_input(**kwargs)
            if input_key in ("pixel_values_flat_video",) and "videos" not in modalities:
                modalities["videos"] = self._parse_and_validate_video_input(**kwargs)
            if (
                input_key
                in (
                    "input_audio_features",
                    "feature_attention_mask",
                    "audio_num_clips",
                )
                and "audios" not in modalities
            ):
                modalities["audios"] = NanoNemotronVLAudioFeatureInputs(
                    **kwargs, validate=False
                )

        return modalities