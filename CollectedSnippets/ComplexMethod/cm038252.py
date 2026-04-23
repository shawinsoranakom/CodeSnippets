def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        for video_idx, video_arr in enumerate(mm_data.get("videos", [])):
            if video_arr.dtype != np.uint8:
                mm_data["videos"][video_idx] = video_arr.astype(np.uint8)

        processed_outputs = self.info.ctx.call_hf_processor(
            hf_processor=self.info.get_hf_processor(**mm_kwargs),
            data=dict(
                text=prompt,
                images=None,
                videos=None,
            ),
        )  # text-only

        if len(mm_data) > 0:
            images = mm_data.get("images")
            videos = mm_data.get("videos")

            # batchify input as a single item
            _processed_outputs = self.info.ctx.call_hf_processor(
                hf_processor=self.info.get_hf_processor(**mm_kwargs),
                data=dict(
                    text=None,
                    images=None if images is None else [images],
                    videos=None if videos is None else [videos],
                ),
            )  # mm-only

            for k, v in _processed_outputs.items():
                if isinstance(v, list) and len(v) > 0:
                    assert len(v) == 1
                    _processed_outputs[k] = v[0]

            if images:
                _processed_outputs["image_sizes_images"] = torch.tensor(
                    _processed_outputs["image_sizes_images"]
                )
                _processed_outputs["vision_query_lengths_images"] = torch.tensor(
                    _processed_outputs["vision_query_lengths_images"]
                )

            if videos:
                _idx_per_video = [
                    0,
                    *accumulate(
                        get_num_combined_frames(len(video)) for video in videos
                    ),
                ]
                _processed_outputs["pixel_values_videos"] = [
                    _processed_outputs["pixel_values_videos"][
                        _idx_per_video[i] : _idx_per_video[i + 1]
                    ]
                    for i in range(len(videos))
                ]
                _processed_outputs["vision_query_lengths_videos"] = [
                    torch.tensor(
                        _processed_outputs["vision_query_lengths_videos"][
                            _idx_per_video[i] : _idx_per_video[i + 1]
                        ]
                    )
                    for i in range(len(videos))
                ]

            processed_outputs.update(_processed_outputs)

        return processed_outputs