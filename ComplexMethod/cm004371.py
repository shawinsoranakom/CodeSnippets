def _preprocess(
        self,
        images: list["torch.Tensor"],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool | None,
        padding_value: float | None,
        padding_mode: str | None,
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> FuyuBatchFeature:
        # Group images by size for batched resizing
        original_image_sizes = [batch_image[0].shape[-2:] for batch_image in images if batch_image]
        grouped_images, grouped_images_index = group_images_by_shape(
            images, disable_grouping=disable_grouping, is_nested=True
        )
        resized_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_resize:
                stacked_images = self.resize(image=stacked_images, size=size, resample=resample)
            resized_images_grouped[shape] = stacked_images
        resized_images = reorder_images(resized_images_grouped, grouped_images_index, is_nested=True)

        image_sizes = [batch_image[0].shape[-2:] for batch_image in resized_images if batch_image]
        image_unpadded_heights = [[image_size[0]] for image_size in image_sizes]
        image_unpadded_widths = [[image_size[1]] for image_size in image_sizes]
        image_scale_factors = [
            [resized_size[0] / original_size[0]]
            for original_size, resized_size in zip(original_image_sizes, image_sizes)
        ]
        if do_pad:
            resized_images = self.pad(
                resized_images,
                pad_size=size,
                fill_value=padding_value,
                padding_mode=padding_mode,
                disable_grouping=disable_grouping,
                is_nested=True,
            )
        # Group images by size for further processing
        # Needed in case do_resize is False, or resize returns images with different sizes
        grouped_images, grouped_images_index = group_images_by_shape(
            resized_images, disable_grouping=disable_grouping, is_nested=True
        )
        processed_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            # Fused rescale and normalize
            stacked_images = self.rescale_and_normalize(
                stacked_images, do_rescale, rescale_factor, do_normalize, image_mean, image_std
            )
            processed_images_grouped[shape] = stacked_images
        processed_images = reorder_images(processed_images_grouped, grouped_images_index, is_nested=True)

        return FuyuBatchFeature(
            data={
                "images": processed_images,
                "image_unpadded_heights": image_unpadded_heights,
                "image_unpadded_widths": image_unpadded_widths,
                "image_scale_factors": image_scale_factors,
            },
            tensor_type=return_tensors,
        )