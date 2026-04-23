def expected_output_image_shape(self, images):
        grid_t = 1
        hidden_dim = self.num_channels * self.temporal_patch_size * self.patch_size * self.patch_size
        seq_len = 0
        for image in images:
            if isinstance(image, list) and isinstance(image[0], Image.Image):
                image = np.stack([np.array(frame) for frame in image])
            elif hasattr(image, "shape"):
                pass
            else:
                image = np.array(image)
            if hasattr(image, "shape") and len(image.shape) >= 3:
                if isinstance(image, np.ndarray):
                    if len(image.shape) == 4:
                        height, width = image.shape[1:3]
                    elif len(image.shape) == 3:
                        height, width = image.shape[:2]
                    else:
                        height, width = self.min_resolution, self.min_resolution
                else:
                    height, width = image.shape[-2:]
            else:
                height, width = self.min_resolution, self.min_resolution

            resized_height, resized_width = smart_resize(
                self.temporal_patch_size,
                height,
                width,
                factor=self.patch_size * self.merge_size,
                min_pixels=self.size["shortest_edge"],
                max_pixels=self.size["longest_edge"],
            )
            grid_h, grid_w = resized_height // self.patch_size, resized_width // self.patch_size
            seq_len += grid_t * grid_h * grid_w
        return (seq_len, hidden_dim)