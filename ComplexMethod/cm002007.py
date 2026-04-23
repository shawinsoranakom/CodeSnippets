def expected_output_image_shape(self, images):
        """
        Returns the expected pixel_values shape for a batch of images.
        PaddleOCRVL outputs patches of shape (N_patches_total, C, patch_size, patch_size).
        """
        seq_len = 0
        for image in images:
            if isinstance(image, Image.Image):
                width, height = image.size
            elif isinstance(image, np.ndarray):
                if image.ndim == 3 and image.shape[2] <= 4:
                    # channels-last: (H, W, C)
                    height, width = image.shape[:2]
                else:
                    # channels-first: (C, H, W)
                    height, width = image.shape[-2:]
            elif is_torch_available() and isinstance(image, torch.Tensor):
                height, width = image.shape[-2:]
            else:
                height, width = self.min_resolution, self.min_resolution

            resized_height, resized_width = smart_resize(
                height,
                width,
                factor=self.patch_size * self.merge_size,
                min_pixels=self.size["shortest_edge"],
                max_pixels=self.size["longest_edge"],
            )
            grid_h = resized_height // self.patch_size
            grid_w = resized_width // self.patch_size
            seq_len += grid_h * grid_w  # temporal_patch_size=1, so grid_t=1

        return (seq_len, self.num_channels, self.patch_size, self.patch_size)