def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        # when the prompt is not empty but the multimodal data is empty,
        # directly invoke the tokenizer.
        if "images" not in mm_data and "videos" not in mm_data and prompt != "":
            tokenizer = self.info.get_tokenizer()
            prompt_ids = tokenizer.encode(prompt)
            tokenizer_output = BatchFeature(
                dict(input_ids=[prompt_ids]), tensor_type="pt"
            )
            return tokenizer_output

        if "images" not in mm_data:
            mm_data["images"] = []
        if "videos" not in mm_data:
            mm_data["videos"] = []

        # Check if HF processor supports video metadata
        hf_processor = self.info.get_hf_processor(**mm_kwargs)
        supports_video_metadata = getattr(
            hf_processor, "supports_video_metadata", False
        )

        if mm_data["videos"] and not supports_video_metadata:
            # Old HF processor, unwrap tuple to pure frames
            logger.warning_once(
                "HF processor doesn't support video metadata. "
                "Timestamps will NOT be rendered. Please upgrade the model."
            )
            mm_data["videos"] = [
                v[0] if isinstance(v, tuple) else v for v in mm_data["videos"]
            ]

        processor_output = self.info.ctx.call_hf_processor(
            hf_processor,
            dict(text=[prompt], images=mm_data["images"], videos=mm_data["videos"]),
            dict(**mm_kwargs, **tok_kwargs),
        )

        # Divide the processor_output into two modalities: image and video.
        if processor_output is not None:
            pixel_values = processor_output["images"]
            if pixel_values is not None:
                processor_output["images"] = self._pixel_values_norm(
                    pixel_values, mm_kwargs
                )
            for key in list(processor_output.keys()):
                if processor_output[key] is None:
                    del processor_output[key]
                    continue
                if key == "grid_thw":
                    grid_thw = processor_output["grid_thw"]
                    pixel_values_all = processor_output["images"]
                    # Identify elements where the first
                    # dimension is greater than 1 and
                    # treat them as the video modality
                    mask = grid_thw[:, 0] > 1
                    processor_output["video_grid_thw"] = grid_thw[mask]
                    processor_output["image_grid_thw"] = grid_thw[~mask]
                    image_patch_num = (
                        processor_output["image_grid_thw"].prod(dim=1).sum()
                    )
                    processor_output["pixel_values"] = pixel_values_all[
                        :image_patch_num
                    ]
                    processor_output["pixel_values_videos"] = pixel_values_all[
                        image_patch_num:
                    ]
                    del processor_output["images"]

        return processor_output