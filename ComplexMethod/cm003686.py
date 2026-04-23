def _preprocess(
        self,
        images: list[list[np.ndarray]],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool | None,
        do_image_splitting: bool | None,
        max_image_size: dict[str, int] | None,
        return_row_col_info: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        """Process a batch of images. Mirrors TorchvisionBackend._preprocess with per-image loops instead of batching."""
        # Resize
        if do_resize:
            images = [
                [self.resize(image=img, size=size, resample=resample) for img in batch_images]
                for batch_images in images
            ]

        # Image splitting
        if do_image_splitting:
            images = [
                [
                    self.resize_for_vision_encoder(image, max_image_size["longest_edge"], resample=resample)
                    for image in batch_images
                ]
                for batch_images in images
            ]
            images_split_arrays = []
            images_rows = []
            images_cols = []
            for batch_images in images:
                split_image_arrays = []
                image_rows = []
                image_cols = []
                for image in batch_images:
                    split_image_array, rows, cols = self.split_images(
                        image, max_image_size=max_image_size, resample=resample
                    )
                    split_image_arrays.extend(split_image_array)
                    image_rows.append(rows)
                    image_cols.append(cols)
                images_split_arrays.append(split_image_arrays)
                images_rows.append(image_rows)
                images_cols.append(image_cols)
            images = images_split_arrays
            rows = images_rows
            cols = images_cols
        else:
            images = [
                [
                    self.resize(
                        image=image,
                        size=SizeDict(height=max_image_size["longest_edge"], width=max_image_size["longest_edge"]),
                        resample=resample,
                    )
                    for image in batch_images
                ]
                for batch_images in images
            ]
            rows = [[0] * len(batch_images) for batch_images in images]
            cols = [[0] * len(batch_images) for batch_images in images]

        # Rescale and normalize
        if do_rescale:
            images = [[self.rescale(img, rescale_factor) for img in batch_images] for batch_images in images]
        if do_normalize:
            images = [[self.normalize(img, image_mean, image_std) for img in batch_images] for batch_images in images]

        # Pad
        if do_pad:
            max_num_images = max(len(images_) for images_ in images)
            max_height, max_width = get_max_height_width(images)
            num_channels = get_num_channels(images)

            padded_images_list = [
                [np.zeros((num_channels, max_height, max_width), dtype=np.float32) for _ in range(max_num_images)]
                for _ in range(len(images))
            ]
            pixel_attention_masks = [
                [np.zeros((max_height, max_width), dtype=np.int64) for _ in range(max_num_images)]
                for _ in range(len(images))
            ]

            for i, batch_images in enumerate(images):
                for j, image in enumerate(batch_images):
                    padded_images_list[i][j], pixel_attention_masks[i][j] = self.pad(image, (max_height, max_width))
            images = padded_images_list

        if do_pad:
            data = {
                "pixel_values": np.array(images),
                "pixel_attention_mask": np.array(pixel_attention_masks),
            }
        elif return_tensors == "pt":
            data = {"pixel_values": np.asarray(images)}
        else:
            data = {"pixel_values": images}

        encoding = BatchFeature(data=data, tensor_type=return_tensors)
        if return_row_col_info:
            encoding["rows"] = rows
            encoding["cols"] = cols

        return encoding