def get_number_of_image_patches(self, height: int, width: int, images_kwargs=None):
        """
        A utility that returns number patches for a given image size.

        Args:
            height (`int`):
                Height of the input image.
            width (`int`):
                Width of the input image.
            images_kwargs (`dict`, *optional*)
                Any kwargs to override defaults of the image processor.
        Returns:
            `int`: Number of patches per image.
        """
        min_patches = images_kwargs.get("min_patches", self.min_patches) if images_kwargs else self.min_patches
        max_patches = images_kwargs.get("max_patches", self.max_patches) if images_kwargs else self.max_patches
        patch_size = images_kwargs.get("patch_size", self.size) if images_kwargs else self.size
        crop_to_patches = (
            images_kwargs.get("crop_to_patches", self.crop_to_patches) if images_kwargs else self.crop_to_patches
        )

        num_patches = 1
        if crop_to_patches and max_patches > 1:
            if isinstance(patch_size, dict):
                patch_height, patch_width = patch_size["height"], patch_size["width"]
            else:
                patch_height, patch_width = patch_size.height, patch_size.width
            num_columns, num_rows = get_optimal_tiled_canvas(
                (height, width), (patch_height, patch_width), min_patches, max_patches
            )
            if num_columns * num_rows > 1:
                num_patches += num_columns * num_rows

        return num_patches