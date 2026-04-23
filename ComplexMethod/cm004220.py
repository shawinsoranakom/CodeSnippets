def _preprocess(
        self,
        images: list[list["torch.Tensor"]],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None",
        do_center_crop: bool,
        crop_size: SizeDict,
        do_rescale: bool,
        rescale_factor: float,
        do_pad: bool,
        pad_size: SizeDict,
        constant_values: float | list[float],
        pad_mode: str,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_flip_channel_order: bool,
        return_tensors: str | TensorType | None,
        disable_grouping: bool | None,
        **kwargs,
    ) -> BatchFeature:
        """
        Preprocess videos using the fast image processor.

        This method processes each video frame through the same pipeline as the original
        TVP image processor but uses torchvision operations for better performance.
        """
        grouped_images, grouped_images_index = group_images_by_shape(
            images, disable_grouping=disable_grouping, is_nested=True
        )
        processed_images_grouped = {}
        for shape, stacked_frames in grouped_images.items():
            # Resize if needed
            if do_resize:
                stacked_frames = self.resize(stacked_frames, size, resample)

            # Center crop if needed
            if do_center_crop:
                stacked_frames = self.center_crop(stacked_frames, crop_size)

            # Rescale and normalize using fused method for consistency
            stacked_frames = self.rescale_and_normalize(
                stacked_frames, do_rescale, rescale_factor, do_normalize, image_mean, image_std
            )

            # Pad if needed
            if do_pad:
                stacked_frames = self.pad(stacked_frames, pad_size, fill_value=constant_values, pad_mode=pad_mode)
                stacked_frames = torch.stack(stacked_frames, dim=0)

            # Flip channel order if needed (RGB to BGR)
            if do_flip_channel_order:
                stacked_frames = self._flip_channel_order(stacked_frames)

            processed_images_grouped[shape] = stacked_frames

        processed_images = reorder_images(processed_images_grouped, grouped_images_index, is_nested=True)
        if return_tensors == "pt":
            processed_images = [torch.stack(images, dim=0) for images in processed_images]
            processed_images = torch.stack(processed_images, dim=0)

        return BatchFeature(data={"pixel_values": processed_images}, tensor_type=return_tensors)