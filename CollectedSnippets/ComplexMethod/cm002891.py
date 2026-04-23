def _preprocess(
        self,
        images: list[np.ndarray],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        patch_size: int,
        temporal_patch_size: int,
        merge_size: int,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        """
        Preprocess images one by one for PIL backend.
        """
        processed_images = []
        processed_grids = []

        for image in images:
            height, width = image.shape[-2:]
            if do_resize:
                resized_height, resized_width = smart_resize(
                    num_frames=temporal_patch_size,
                    height=height,
                    width=width,
                    temporal_factor=temporal_patch_size,
                    factor=patch_size * merge_size,
                    min_pixels=size.shortest_edge,
                    max_pixels=size.longest_edge,
                )
                image = self.resize(
                    image,
                    size=SizeDict(height=resized_height, width=resized_width),
                    resample=resample,
                )

            # Rescale and normalize
            if do_rescale:
                image = self.rescale(image, rescale_factor)
            if do_normalize:
                image = self.normalize(image, image_mean, image_std)

            # Ensure float32 for patch processing
            image_array = np.asarray(image, dtype=np.float32)
            if image_array.ndim == 3:  # (C, H, W)
                image_array = np.expand_dims(image_array, axis=0)  # (1, C, H, W)
            if image_array.ndim == 4:  # (B, C, H, W)
                image_array = np.expand_dims(image_array, axis=1)  # (B, T=1, C, H, W)

            resized_height, resized_width = image_array.shape[-2:]

            if image_array.shape[1] % temporal_patch_size != 0:
                repeats = np.repeat(
                    image_array[:, -1:],
                    temporal_patch_size - (image_array.shape[1] % temporal_patch_size),
                    axis=1,
                )
                image_array = np.concatenate([image_array, repeats], axis=1)

            batch_size, t_len, channel = image_array.shape[:3]
            grid_t = t_len // temporal_patch_size
            grid_h, grid_w = resized_height // patch_size, resized_width // patch_size

            patches = image_array.reshape(
                batch_size,
                grid_t,
                temporal_patch_size,
                channel,
                grid_h // merge_size,
                merge_size,
                patch_size,
                grid_w // merge_size,
                merge_size,
                patch_size,
            )
            # (B, grid_t, gh, gw, mh, mw, C, tp, ph, pw)
            patches = np.transpose(patches, (0, 1, 4, 7, 5, 8, 3, 2, 6, 9))

            flatten_patches = patches.reshape(
                batch_size,
                grid_t * grid_h * grid_w,
                channel * temporal_patch_size * patch_size * patch_size,
            )

            # Remove batch dimension and append: shape is (seq_len, hidden_dim)
            processed_images.append(flatten_patches.squeeze(0))
            processed_grids.append([grid_t, grid_h, grid_w])

        # Concatenate all images along sequence dimension: (total_seq_len, hidden_dim)
        pixel_values = np.concatenate(processed_images, axis=0)
        image_grid_thw = np.array(processed_grids)

        return BatchFeature(
            data={"pixel_values": pixel_values, "image_grid_thw": image_grid_thw}, tensor_type=return_tensors
        )