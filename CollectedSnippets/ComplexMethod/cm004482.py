def _preprocess(
        self,
        images: list["torch.Tensor"],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None",
        do_center_crop: bool,
        crop_size: SizeDict,
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        crop_to_patches: bool = False,
        min_patches: int = 1,
        max_patches: int = 12,
        use_covering_area_grid: bool = True,
        **kwargs,
    ) -> BatchFeature:
        if crop_to_patches and max_patches > 1:
            grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
            processed_images_grouped = {}
            grids = {}
            for shape, stacked_images in grouped_images.items():
                stacked_images, grid = self.crop_image_to_patches(
                    stacked_images,
                    min_patches,
                    max_patches,
                    patch_size=size,
                    use_covering_area_grid=use_covering_area_grid,
                    resample=resample,
                )
                processed_images_grouped[shape] = stacked_images
                grids[shape] = grid
            images = reorder_images(processed_images_grouped, grouped_images_index)
            images = [image for images_list in images for image in images_list]
            grids = reorder_images(grids, grouped_images_index)
        else:
            grids = [[1, 1] for _ in range(len(images))]

        # Group images by size for batched resizing
        grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
        resized_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_resize:
                stacked_images = self.resize(image=stacked_images, size=size, resample=resample)
            resized_images_grouped[shape] = stacked_images
        resized_images = reorder_images(resized_images_grouped, grouped_images_index)

        # Group images by size for further processing
        # Needed in case do_resize is False, or resize returns images with different sizes
        grouped_images, grouped_images_index = group_images_by_shape(resized_images, disable_grouping=disable_grouping)
        processed_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_center_crop:
                stacked_images = self.center_crop(stacked_images, crop_size)
            # Fused rescale and normalize
            stacked_images = self.rescale_and_normalize(
                stacked_images, do_rescale, rescale_factor, do_normalize, image_mean, image_std
            )
            processed_images_grouped[shape] = stacked_images

        processed_images = reorder_images(processed_images_grouped, grouped_images_index)
        return BatchFeature(data={"pixel_values": processed_images, "grids": grids}, tensor_type=return_tensors)