def _preprocess(
        self,
        videos: list["torch.Tensor"],
        do_convert_rgb: bool,
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        do_pad: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        return_tensors: str | TensorType | None = None,
        **kwargs,
    ):
        grouped_videos, grouped_videos_index = group_videos_by_shape(videos)
        resized_videos_grouped = {}
        for shape, stacked_videos in grouped_videos.items():
            if do_convert_rgb:
                stacked_videos = self.convert_to_rgb(stacked_videos)
            if do_resize:
                stacked_videos = self.resize(stacked_videos, size=size, resample=resample)
            resized_videos_grouped[shape] = stacked_videos
        resized_videos = reorder_videos(resized_videos_grouped, grouped_videos_index)

        grouped_videos, grouped_videos_index = group_videos_by_shape(resized_videos)
        processed_videos_grouped = {}
        for shape, stacked_videos in grouped_videos.items():
            stacked_videos = self.rescale_and_normalize(
                stacked_videos, do_rescale, rescale_factor, do_normalize, image_mean, image_std
            )
            processed_videos_grouped[shape] = stacked_videos

        processed_videos = reorder_videos(processed_videos_grouped, grouped_videos_index)

        if do_pad:
            pad_size = get_max_height_width(processed_videos)
            max_num_frames = max(len(video) for video in processed_videos)
            grouped_videos, grouped_videos_index = group_videos_by_shape(processed_videos)
            processed_padded_mask_grouped = {}
            processed_videos_grouped = {}

            for shape, stacked_videos in grouped_videos.items():
                stacked_videos, padded_masks = self.pad(
                    stacked_videos, padded_size=pad_size, max_num_frames=max_num_frames
                )
                processed_videos_grouped[shape] = stacked_videos
                processed_padded_mask_grouped[shape] = padded_masks

            processed_videos = reorder_videos(processed_videos_grouped, grouped_videos_index)
            pixel_attention_mask = reorder_videos(processed_padded_mask_grouped, grouped_videos_index)

        data = {"pixel_values": processed_videos}

        if do_pad:
            data["pixel_attention_mask"] = (
                torch.stack(pixel_attention_mask, dim=0)
                if do_pad and return_tensors is not None
                else pixel_attention_mask
            )
        return BatchFeature(data, tensor_type=return_tensors)