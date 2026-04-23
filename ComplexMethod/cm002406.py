def pad(
        self,
        images: list[np.ndarray],
        pad_size: SizeDict = None,
        fill_value: int | None = 0,
        padding_mode: str | None = "constant",
        return_mask: bool = False,
        **kwargs,
    ) -> tuple[list[np.ndarray], list[np.ndarray]] | list[np.ndarray]:
        """Pad images to specified size using NumPy."""
        if pad_size is not None:
            if not (pad_size.height and pad_size.width):
                raise ValueError(f"Pad size must contain 'height' and 'width' keys only. Got pad_size={pad_size}.")
            target_height, target_width = pad_size.height, pad_size.width
        else:
            target_height, target_width = get_max_height_width(images)

        processed_images = []
        processed_masks = []

        for image in images:
            height, width = get_image_size(image, channel_dim=ChannelDimension.FIRST)
            padding_height = target_height - height
            padding_width = target_width - width

            if padding_height < 0 or padding_width < 0:
                raise ValueError(
                    f"Padding dimensions are negative. Please make sure that the `pad_size` is larger than the "
                    f"image size. Got pad_size=({target_height}, {target_width}), image_size=({height}, {width})."
                )

            if height != target_height or width != target_width:
                # Pad format: ((before_1, after_1), (before_2, after_2), ...)
                # For CHW format: ((0, 0), (0, padding_height), (0, padding_width))
                pad_width = ((0, 0), (0, padding_height), (0, padding_width))
                if padding_mode == "constant":
                    image = np.pad(image, pad_width, mode="constant", constant_values=fill_value)
                else:
                    image = np.pad(image, pad_width, mode=padding_mode)

            processed_images.append(image)

            if return_mask:
                mask = np.zeros((target_height, target_width), dtype=np.int64)
                mask[:height, :width] = 1
                processed_masks.append(mask)

        if return_mask:
            return processed_images, processed_masks
        return processed_images