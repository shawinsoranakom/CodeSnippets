def _preprocess(
        self,
        images: list["torch.Tensor"],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        do_split_image: bool,
        do_pad: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        disable_grouping: bool | None,
        **kwargs,
    ):
        """Preprocesses the input images and masks if provided."""
        patch_offsets = []

        grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
        resized_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_resize:
                stacked_images = self.resize(image=stacked_images, size=size, resample=resample)
            resized_images_grouped[shape] = stacked_images
        images = reorder_images(resized_images_grouped, grouped_images_index)

        if do_split_image:
            grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
            patches, patch_offsets = [], []
            for shape, stacked_images in grouped_images.items():
                original_indices = [
                    original_idx for original_idx, (img_shape, _) in grouped_images_index.items() if img_shape == shape
                ]
                split_patches, offsets = self._split_image(stacked_images, size, original_indices)
                patches.extend(split_patches)
                patch_offsets.extend(offsets)
            images, patch_offsets = reorder_patches_and_offsets(patches, patch_offsets)

        if do_pad:
            grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
            padded_grouped = {
                shape: self._pad(stacked_images, size) for shape, stacked_images in grouped_images.items()
            }
            images = reorder_images(padded_grouped, grouped_images_index)

        grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
        processed_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            stacked_images = self.rescale_and_normalize(
                stacked_images, do_rescale, rescale_factor, do_normalize, image_mean, image_std
            )
            processed_images_grouped[shape] = stacked_images
        processed_images = reorder_images(processed_images_grouped, grouped_images_index)

        return processed_images, patch_offsets