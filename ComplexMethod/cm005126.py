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
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        do_pan_and_scan: bool | None = None,
        pan_and_scan_min_crop_size: int | None = None,
        pan_and_scan_max_num_crops: int | None = None,
        pan_and_scan_min_ratio_to_activate: float | None = None,
        **kwargs,
    ) -> BatchFeature:
        # Group images by size for batched processing
        processed_images_grouped = {}
        num_crops_grouped = {}
        grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
        for shape_images, stacked_images in grouped_images.items():
            if do_pan_and_scan:
                pas_images, num_crops = self._process_images_for_pan_and_scan(
                    images=stacked_images,
                    do_pan_and_scan=do_pan_and_scan,
                    pan_and_scan_min_crop_size=pan_and_scan_min_crop_size,
                    pan_and_scan_max_num_crops=pan_and_scan_max_num_crops,
                    pan_and_scan_min_ratio_to_activate=pan_and_scan_min_ratio_to_activate,
                )
                # Add the thumbnails to the image patches
                stacked_images = [stacked_images] + pas_images
                # Group images by size for batched resizing (this will typically group thumbnails together and cropped patches together)
                processed_image_patches_grouped = {}
                grouped_image_patches, grouped_image_patches_index = group_images_by_shape(
                    stacked_images, disable_grouping=disable_grouping
                )
                for shape, stacked_image_patches in grouped_image_patches.items():
                    stacked_image_patches = self.resize(
                        image=stacked_image_patches,
                        size=size,
                        resample=resample,
                    )
                    processed_image_patches_grouped[shape] = stacked_image_patches
                processed_image_patches = reorder_images(processed_image_patches_grouped, grouped_image_patches_index)
                # Transpose to have the thumbnails with their corresponding patches
                stacked_images = torch.stack(processed_image_patches, dim=0).transpose(0, 1).contiguous()
            else:
                num_crops = [0 for _ in stacked_images]

                if do_resize:
                    stacked_images = self.resize(
                        image=stacked_images,
                        size=size,
                        resample=resample,
                    )
            num_crops_grouped[shape_images] = num_crops
            processed_images_grouped[shape_images] = stacked_images
        resized_images = reorder_images(processed_images_grouped, grouped_images_index)
        # If pan and scan is enabled, we need to flatten the list of images
        if do_pan_and_scan:
            resized_images = [image for images_list in resized_images for image in images_list]
        num_crops = reorder_images(num_crops_grouped, grouped_images_index)

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
        return BatchFeature(
            data={"pixel_values": processed_images, "num_crops": num_crops}, tensor_type=return_tensors
        )