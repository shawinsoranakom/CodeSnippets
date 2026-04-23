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
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        do_align_long_axis: bool = False,
        do_thumbnail: bool = True,
        do_crop_margin: bool = True,
        **kwargs,
    ) -> BatchFeature:
        # Crop images
        if do_crop_margin:
            images = [self.crop_margin(image) for image in images]

        # Group images by size for batched resizing
        grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
        resized_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_align_long_axis:
                stacked_images = self.align_long_axis(image=stacked_images, size=size)
            if do_resize:
                stacked_images = self.resize(image=stacked_images, size=size, resample=resample)
            if do_thumbnail:
                stacked_images = self.thumbnail(image=stacked_images, size=size)
            if do_pad:
                stacked_images = self.pad_images(image=stacked_images, size=size)
            resized_images_grouped[shape] = stacked_images
        resized_images = reorder_images(resized_images_grouped, grouped_images_index)

        # Group images by size for further processing
        # Needed in case do_resize is False, or resize returns images with different sizes
        grouped_images, grouped_images_index = group_images_by_shape(resized_images, disable_grouping=disable_grouping)
        processed_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            # Fused rescale and normalize
            stacked_images = self.rescale_and_normalize(
                stacked_images, do_rescale, rescale_factor, do_normalize, image_mean, image_std
            )
            processed_images_grouped[shape] = stacked_images

        processed_images = reorder_images(processed_images_grouped, grouped_images_index)

        return BatchFeature(data={"pixel_values": processed_images}, tensor_type=return_tensors)