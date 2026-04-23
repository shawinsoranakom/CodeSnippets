def _get_num_multimodal_tokens(self, image_sizes=None, **kwargs):
        """
        Computes the number of placeholder tokens needed for multimodal inputs with the given sizes.
        Args:
            image_sizes (list[list[str]], *optional*):
                The input sizes formatted as (height, width) per each image.
        Returns:
            `MultiModalData`: A `MultiModalData` object holding number of tokens per each of the provided
            input modalities, along with other useful data.
        """
        vision_data = {}
        if image_sizes is not None:
            images_kwargs = LlavaNextProcessorKwargs._defaults.get("images_kwargs", {})
            images_kwargs.update(kwargs)

            size = images_kwargs.get("size", None) or self.image_processor.size
            if isinstance(size, SizeDict):
                size = (
                    (size.shortest_edge, size.shortest_edge)
                    if size.shortest_edge is not None
                    else (min(size.height, size.width), min(size.height, size.width))
                )
            else:
                size = (
                    (size["shortest_edge"], size["shortest_edge"])
                    if "shortest_edge" in size
                    else (min(size["height"], size["width"]), min(size["height"], size["width"]))
                )
            processed_height, processed_width = size

            batch_num_image_tokens = []
            num_image_patches = [1] * len(image_sizes)  # llava-next doesn't batch pixels as Idefics, thus `1` patch`
            for image_size in image_sizes:
                orig_height, orig_width = image_size
                num_image_tokens = self._get_number_of_features(
                    orig_height, orig_width, processed_height, processed_width
                )
                if self.vision_feature_select_strategy == "default":
                    num_image_tokens -= 1
                batch_num_image_tokens.append(num_image_tokens)
            vision_data.update({"num_image_tokens": batch_num_image_tokens, "num_image_patches": num_image_patches})

        return MultiModalData(**vision_data)