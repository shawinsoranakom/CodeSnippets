def _get_num_multimodal_tokens(self, image_sizes=None, **kwargs):
        """
        Computes the number of placeholder tokens needed for multimodal inputs with the given sizes.

        Args:
            image_sizes (`list[list[int]]`, *optional*):
                The input sizes formatted as (height, width) per each image.

        Returns:
            `MultiModalData`: A `MultiModalData` object holding number of tokens per each of the provided
            input modalities, along with other useful data.
        """
        vision_data = {}
        if image_sizes is not None:
            images_kwargs = LightOnOcrProcessorKwargs._defaults.get("images_kwargs", {})
            images_kwargs.update(kwargs)

            size = images_kwargs.get("size", None) or self.image_processor.size
            patch_size = images_kwargs.get("patch_size", None) or self.image_processor.patch_size
            if isinstance(patch_size, dict) and "height" in patch_size and "width" in patch_size:
                patch_size = (patch_size["height"], patch_size["width"])

            num_image_tokens = []
            for height, width in image_sizes:
                resized_height, resized_width = get_resize_output_image_size(
                    np.zeros((height, width, 3)),
                    size=(size["longest_edge"], size["longest_edge"]),
                    patch_size=patch_size,
                )
                num_height_tokens = resized_height // self.effective_patch_size
                num_width_tokens = resized_width // self.effective_patch_size
                num_image_tokens.append(num_width_tokens * num_height_tokens)

            num_image_patches = [1] * len(image_sizes)
            vision_data.update({"num_image_tokens": num_image_tokens, "num_image_patches": num_image_patches})

        return MultiModalData(**vision_data)