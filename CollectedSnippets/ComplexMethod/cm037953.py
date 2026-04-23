def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        mm_data = dict(mm_data)
        videos = mm_data.pop("videos", [])
        assert isinstance(videos, list)

        if not videos:
            return super()._call_hf_processor(
                prompt=prompt,
                mm_data=mm_data,
                mm_kwargs=mm_kwargs,
                tok_kwargs=tok_kwargs,
            )

        # LLaVA-OneVision processor doesn't support multiple videos
        # with different sizes when converting back to tensors
        # So, we process each component separately
        # NOTE: No prompt replacement is applied in this case
        processor = self.info.get_hf_processor()
        image_token = processor.image_token
        video_token = processor.video_token

        text_outputs = super()._call_hf_processor(
            prompt=prompt,
            mm_data={},
            mm_kwargs=mm_kwargs,
            tok_kwargs=tok_kwargs,
        )

        images = mm_data.pop("images", [])
        assert isinstance(images, list)
        if images:
            processor_outputs = super()._call_hf_processor(
                prompt=image_token * len(images),
                mm_data={"images": images},
                mm_kwargs=mm_kwargs,
                tok_kwargs=tok_kwargs,
            )
            image_outputs = {
                k: v
                for k, v in processor_outputs.items()
                if k in ("pixel_values", "image_sizes")
            }
        else:
            image_outputs = {}

        pixel_values_videos = []
        for video in videos:
            item_outputs = super()._call_hf_processor(
                prompt=video_token,
                mm_data={"videos": video},
                mm_kwargs=mm_kwargs,
                tok_kwargs=tok_kwargs,
            )

            pixel_values_videos.append(item_outputs["pixel_values_videos"][0])

        video_outputs = {"pixel_values_videos": pixel_values_videos}

        combined_outputs = dict(
            text_outputs,
            **image_outputs,
            **video_outputs,
        )
        return BatchFeature(combined_outputs)