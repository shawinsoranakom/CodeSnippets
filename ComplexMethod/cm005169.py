def _preprocess(
        self,
        images: list["torch.Tensor"],
        do_resize: bool,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float],
        image_std: float | list[float],
        downsample_factor: int,
        do_image_splitting: bool,
        min_tiles: int,
        max_tiles: int,
        use_thumbnail: bool,
        min_image_tokens: int,
        max_image_tokens: int,
        encoder_patch_size: int,
        tile_size: int,
        max_pixels_tolerance: float,
        do_pad: bool,
        return_row_col_info: bool,
        return_tensors: str | TensorType | None,
        disable_grouping: bool | None,
        **kwargs,
    ) -> BatchFeature:
        if not do_image_splitting:
            min_tiles = 1
            max_tiles = 1
            logger.debug(
                "Image splitting is disabled, setting min_tiles and max_tiles to 1. Set do_image_splitting=True to enable splitting."
            )

        if do_image_splitting and min_tiles > max_tiles:
            raise ValueError("min_tiles must be less than or equal to max_tiles")

        max_thumbnail_image_patches = max_image_tokens * downsample_factor**2
        tile_size_patches = (tile_size // encoder_patch_size) ** 2 if do_image_splitting else 0
        max_num_patches = max(
            max_thumbnail_image_patches,
            tile_size_patches,
        )

        grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
        resized_images_grouped = {}
        resized_image_sizes = {}
        rows_grouped, cols_grouped = {}, {}
        for shape, stacked_images in grouped_images.items():
            num_rows = [1] * stacked_images.shape[0]
            num_cols = [1] * stacked_images.shape[0]
            height, width = stacked_images.shape[-2:]
            image_sizes = [[height, width]] * stacked_images.shape[0]
            do_resize = True

            if do_resize:
                stacked_images, num_rows, num_cols, image_sizes = self.resize_and_split(
                    stacked_images,
                    downsample_factor=downsample_factor,
                    min_tiles=min_tiles,
                    max_tiles=max_tiles,
                    use_thumbnail=use_thumbnail,
                    min_image_tokens=min_image_tokens,
                    max_image_tokens=max_image_tokens,
                    encoder_patch_size=encoder_patch_size,
                    tile_size=tile_size,
                    max_pixels_tolerance=max_pixels_tolerance,
                    resample=resample,
                )

            rows_grouped[shape] = num_rows
            cols_grouped[shape] = num_cols
            resized_image_sizes[shape] = image_sizes
            resized_images_grouped[shape] = stacked_images
        resized_images = reorder_images(resized_images_grouped, grouped_images_index)
        batch_rows = reorder_images(rows_grouped, grouped_images_index)
        batch_cols = reorder_images(cols_grouped, grouped_images_index)
        resized_image_sizes = reorder_images(resized_image_sizes, grouped_images_index)

        grouped_images, grouped_images_index = group_images_by_shape(
            resized_images, disable_grouping=disable_grouping, is_nested=True
        )

        processed_images_grouped = {}
        processed_masks, processed_spatial_shapes = {}, {}
        for shape, stacked_images in grouped_images.items():
            # Fused rescale and normalize
            stacked_images = self.rescale_and_normalize(
                stacked_images, do_rescale, rescale_factor, do_normalize, image_mean, image_std
            )
            batch_size, *_, height, width = stacked_images.shape
            num_patches_height = height // encoder_patch_size
            num_patches_width = width // encoder_patch_size

            stacked_images = convert_image_to_patches(stacked_images, encoder_patch_size)
            processed_spatial_shapes[shape] = [[num_patches_height, num_patches_width]] * batch_size

            if do_pad:
                stacked_images, pixel_mask = pad_along_first_dim(stacked_images, max_num_patches)
                processed_masks[shape] = [pixel_mask] * batch_size

            processed_images_grouped[shape] = stacked_images

        processed_images = reorder_images(processed_images_grouped, grouped_images_index, is_nested=True)
        data = {"pixel_values": torch.cat([torch.stack(images) for images in processed_images])}

        if do_pad:
            processed_masks = reorder_images(processed_masks, grouped_images_index, is_nested=True)
            processed_spatial_shapes = reorder_images(processed_spatial_shapes, grouped_images_index, is_nested=True)
            processed_masks = torch.cat([torch.stack(masks) for masks in processed_masks])
            processed_spatial_shapes = torch.cat(
                [torch.tensor(spatial_shape) for spatial_shape in processed_spatial_shapes]
            )
            data.update({"pixel_attention_mask": processed_masks, "spatial_shapes": processed_spatial_shapes})

        if return_row_col_info:
            data["image_rows"] = batch_rows
            data["image_cols"] = batch_cols
            data["image_sizes"] = resized_image_sizes

        encoding = BatchFeature(data=data, tensor_type=return_tensors)
        return encoding