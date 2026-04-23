def _preprocess(
        self,
        images: list["torch.Tensor"],
        batch_num_images: list[int],
        do_resize: bool,
        size: SizeDict,
        image_grid_pinpoints: list[list[int]],
        resample: "PILImageResampling | None",
        do_center_crop: bool,
        crop_size: SizeDict,
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool,
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        processed_images = []
        image_sizes = []

        # only single image patching is supported
        need_patching = [n == 1 for n in batch_num_images for _ in range(n)]

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

        for i, image in enumerate(images):
            if need_patching[i]:
                image_patches = self._get_image_patches(
                    image,
                    image_grid_pinpoints,
                    size=size_tuple,
                    patch_size=patch_size,
                    resample=resample,
                )
            else:
                padded_image = self.pad_to_square(
                    images=image, background_color=tuple(int(x * 255) for x in self.image_mean)
                )
                image_patches = [padded_image]

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
                stacked_image_patches = self.rescale_and_normalize(
                    stacked_image_patches, do_rescale, rescale_factor, do_normalize, image_mean, image_std
                )
                processed_image_patches_grouped[shape] = stacked_image_patches
            processed_image_patches = reorder_images(processed_image_patches_grouped, grouped_image_patches_index)
            processed_image_patches = torch.stack(processed_image_patches, dim=0)
            processed_images.append(processed_image_patches)
            image_sizes.append(get_image_size(image, ChannelDimension.FIRST))

        if do_pad:
            processed_images = self._pad_for_batching(processed_images)
        return BatchFeature(
            data={"pixel_values": processed_images, "image_sizes": image_sizes, "batch_num_images": batch_num_images},
            tensor_type=return_tensors,
        )