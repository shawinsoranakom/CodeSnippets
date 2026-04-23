def _preprocess(
        self,
        images: list[list["torch.Tensor"]],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool | None,
        do_image_splitting: bool | None,
        max_image_size: dict[str, int] | None,
        return_row_col_info: bool | None,
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        """
        Process a batch of images for the model.
        """

        grouped_images, grouped_images_index = group_images_by_shape(
            images, is_nested=True, disable_grouping=disable_grouping
        )
        resized_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_resize:
                stacked_images = self.resize(stacked_images, size, resample=resample)
            resized_images_grouped[shape] = stacked_images
        resized_images = reorder_images(resized_images_grouped, grouped_images_index, is_nested=True)

        grouped_images, grouped_images_index = group_images_by_shape(
            resized_images, is_nested=True, disable_grouping=disable_grouping
        )
        split_images_grouped = {}
        if do_image_splitting:
            rows_grouped = {}
            cols_grouped = {}
            for shape, stacked_images in grouped_images.items():
                stacked_images = self.resize_for_vision_encoder(
                    stacked_images, max_image_size["longest_edge"], resample=resample
                )
                stacked_images, rows, cols = self.split_images(
                    stacked_images, max_image_size=max_image_size, resample=resample
                )
                split_images_grouped[shape] = stacked_images
                rows_grouped[shape] = rows
                cols_grouped[shape] = cols
            processed_images = reorder_images(split_images_grouped, grouped_images_index, is_nested=True)
            rows = reorder_images(rows_grouped, grouped_images_index, is_nested=True)
            cols = reorder_images(cols_grouped, grouped_images_index, is_nested=True)
            # flattenened the doubly nested list to a nested list
            for i, group_images in enumerate(processed_images):
                processed_images[i] = [image for sublist in group_images for image in sublist]
        else:
            for shape, stacked_images in grouped_images.items():
                # We square the images to max_image_size
                stacked_images = self.resize(
                    image=stacked_images,
                    size=SizeDict(height=max_image_size["longest_edge"], width=max_image_size["longest_edge"]),
                    resample=resample,
                )
                split_images_grouped[shape] = stacked_images
            processed_images = reorder_images(split_images_grouped, grouped_images_index, is_nested=True)
            rows = [[0] * len(images) for images in processed_images]
            cols = [[0] * len(images) for images in processed_images]
        # Group images by size for further processing
        # Needed in case do_resize is False, or resize returns images with different sizes
        grouped_images, grouped_images_index = group_images_by_shape(
            processed_images, is_nested=True, disable_grouping=disable_grouping
        )
        processed_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            # Fused rescale and normalize
            stacked_images = self.rescale_and_normalize(
                stacked_images, do_rescale, rescale_factor, do_normalize, image_mean, image_std
            )
            processed_images_grouped[shape] = stacked_images
        processed_images = reorder_images(processed_images_grouped, grouped_images_index, is_nested=True)
        if do_pad:
            # Get max images per batch
            max_num_images = max(len(images_) for images_ in processed_images)
            max_height, max_width = get_max_height_width(processed_images)
            num_channels = get_num_channels(processed_images)
            device = get_device_from_images(processed_images)

            processed_images_padded = torch.zeros(
                len(processed_images),
                max_num_images,
                *(num_channels, max_height, max_width),
                device=device,
            )
            pixel_attention_masks = torch.zeros(
                len(processed_images),
                max_num_images,
                *(max_height, max_width),
                device=device,
            )
            for i, images in enumerate(processed_images):
                for j, image in enumerate(images):
                    processed_images_padded[i, j], pixel_attention_masks[i, j] = self.pad(
                        image, (max_height, max_width)
                    )
            processed_images = processed_images_padded

        if do_pad:
            data = {"pixel_values": processed_images, "pixel_attention_mask": pixel_attention_masks}
        elif return_tensors == "pt":
            data = {"pixel_values": torch.stack([torch.stack(images) for images in processed_images])}
        else:
            data = {"pixel_values": processed_images}
        # This is needed for generating correct text inputs in the processor - we don't pad to the max number of images
        encoding = BatchFeature(data=data, tensor_type=return_tensors)

        if return_row_col_info:
            encoding["rows"] = rows
            encoding["cols"] = cols

        return encoding