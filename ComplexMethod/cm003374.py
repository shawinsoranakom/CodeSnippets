def pad(
        self,
        images: list[np.ndarray],
        padded_size: tuple[int, int],
        segmentation_maps: list[np.ndarray] | None = None,
        fill: int = 0,
        ignore_index: int = 255,
    ) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray] | None]:
        """
        Pad images and optionally segmentation maps to the given size.

        Args:
            images (`list[np.ndarray]`):
                Images to pad.
            padded_size (`tuple[int, int]`):
                Target size (height, width) to pad to.
            segmentation_maps (`list[np.ndarray]`, *optional*):
                Segmentation maps to pad.
            fill (`int`, *optional*, defaults to 0):
                Fill value for images.
            ignore_index (`int`, *optional*, defaults to 255):
                Fill value for segmentation maps.

        Returns:
            `tuple`: (padded_images, pixel_masks, padded_segmentation_maps)
        """
        padded_images = []
        pixel_masks = []

        for image in images:
            original_size = image.shape[-2:]
            padding_bottom = padded_size[0] - original_size[0]
            padding_right = padded_size[1] - original_size[1]
            if padding_bottom < 0 or padding_right < 0:
                raise ValueError(
                    f"Padding dimensions are negative. Please make sure that the padded size is larger than the "
                    f"original size. Got padded size: {padded_size}, original size: {original_size}."
                )
            if original_size != padded_size:
                padding = ((0, padding_bottom), (0, padding_right))
                image = np_pad(
                    image,
                    padding,
                    mode=PaddingMode.CONSTANT,
                    constant_values=fill,
                    data_format=ChannelDimension.FIRST,
                    input_data_format=ChannelDimension.FIRST,
                )
            padded_images.append(image)

            # Make a pixel mask for the image
            pixel_mask = np.zeros(padded_size, dtype=np.int64)
            pixel_mask[: original_size[0], : original_size[1]] = 1
            pixel_masks.append(pixel_mask)

        padded_segmentation_maps = None
        if segmentation_maps is not None:
            padded_segmentation_maps = []
            for mask in segmentation_maps:
                original_size = mask.shape[-2:]
                padding_bottom = padded_size[0] - original_size[0]
                padding_right = padded_size[1] - original_size[1]
                if original_size != padded_size:
                    padding = ((0, padding_bottom), (0, padding_right))
                    mask = np_pad(
                        mask,
                        padding,
                        mode=PaddingMode.CONSTANT,
                        constant_values=ignore_index,
                        data_format=ChannelDimension.FIRST,
                        input_data_format=ChannelDimension.FIRST,
                    )
                padded_segmentation_maps.append(mask)

        return padded_images, pixel_masks, padded_segmentation_maps