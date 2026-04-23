def _preprocess(
        self,
        images: list["torch.Tensor"],
        do_resize: bool,
        size: SizeDict,
        image_grid_pinpoints: list[list[int]],
        resample: "PILImageResampling | tvF.InterpolationMode | int | None",
        do_center_crop: bool,
        crop_size: SizeDict,
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool | None,
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        """Custom preprocessing for LLaVA-NeXT with patch processing."""
        processed_images = []
        image_sizes = []

        # Backend's resize method handles resample conversion, so we can pass it directly
        # Determine the size tuple
        if size and size.height and size.width:
            size_tuple = (size.height, size.width)
        else:
            size_tuple = (size.shortest_edge, size.shortest_edge)

        # Determine the patch size
        if crop_size and crop_size.height:
            patch_size = crop_size.height
        elif size and size.height:
            patch_size = size.height
        else:
            patch_size = size.shortest_edge

        for image in images:
            image_patches = self._get_image_patches(
                image,
                image_grid_pinpoints,
                size=size_tuple,
                patch_size=patch_size,
                resample=resample,
            )

            # Group images by size for batched processing
            processed_image_patches_grouped = {}
            grouped_image_patches, grouped_image_patches_index = group_images_by_shape(
                image_patches, disable_grouping=disable_grouping
            )
            for shape, stacked_image_patches in grouped_image_patches.items():
                if do_resize:
                    stacked_image_patches = self.resize(
                        image=stacked_image_patches,
                        size=size,
                        resample=resample,
                    )
                if do_center_crop:
                    stacked_image_patches = self.center_crop(stacked_image_patches, crop_size)
                # Fused rescale and normalize
                # Convert lists to tuples for lru_cache compatibility
                image_mean_tuple = tuple(image_mean) if isinstance(image_mean, list) else image_mean
                image_std_tuple = tuple(image_std) if isinstance(image_std, list) else image_std
                stacked_image_patches = self.rescale_and_normalize(
                    stacked_image_patches, do_rescale, rescale_factor, do_normalize, image_mean_tuple, image_std_tuple
                )
                processed_image_patches_grouped[shape] = stacked_image_patches
            processed_image_patches = reorder_images(processed_image_patches_grouped, grouped_image_patches_index)
            processed_image_patches = torch.stack(processed_image_patches, dim=0)
            processed_images.append(processed_image_patches)
            image_sizes.append(get_image_size(image, ChannelDimension.FIRST))

        if do_pad:
            processed_images = self._pad_for_batching(processed_images)

        return BatchFeature(
            data={"pixel_values": processed_images, "image_sizes": image_sizes}, tensor_type=return_tensors
        )