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
        do_color_quantize: bool | None = None,
        clusters: list | np.ndarray | torch.Tensor | None = None,
        **kwargs,
    ):
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

        pixel_values = reorder_images(processed_images_grouped, grouped_images_index)

        # If color quantization is requested, perform it; otherwise return pixel values
        if do_color_quantize:
            # Prepare clusters
            if clusters is None:
                raise ValueError("Clusters must be provided for color quantization.")
            # Convert to torch tensor if needed (clusters might be passed as list/numpy)
            clusters_torch = (
                torch.as_tensor(clusters, dtype=torch.float32) if not isinstance(clusters, torch.Tensor) else clusters
            ).to(pixel_values[0].device, dtype=pixel_values[0].dtype)

            # Group images by shape for batch processing
            # We need to check if the pixel values are a tensor or a list of tensors
            grouped_images, grouped_images_index = group_images_by_shape(
                pixel_values, disable_grouping=disable_grouping
            )
            # Process each group
            input_ids_grouped = {}

            for shape, stacked_images in grouped_images.items():
                input_ids = color_quantize_torch(
                    stacked_images.permute(0, 2, 3, 1).reshape(-1, 3), clusters_torch
                )  # (B*H*W, C)
                input_ids_grouped[shape] = input_ids.reshape(stacked_images.shape[0], -1).reshape(
                    stacked_images.shape[0], -1
                )  # (B, H, W)

            input_ids = reorder_images(input_ids_grouped, grouped_images_index)

            return BatchFeature(data={"input_ids": input_ids}, tensor_type=return_tensors)

        return BatchFeature(data={"pixel_values": pixel_values}, tensor_type=return_tensors)