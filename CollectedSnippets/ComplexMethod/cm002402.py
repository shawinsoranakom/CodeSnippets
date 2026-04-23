def pad(
        self,
        images: list["torch.Tensor"],
        pad_size: SizeDict = None,
        fill_value: int | None = 0,
        padding_mode: str | None = "constant",
        return_mask: bool = False,
        disable_grouping: bool | None = False,
        is_nested: bool | None = False,
        **kwargs,
    ) -> Union[tuple["torch.Tensor", "torch.Tensor"], "torch.Tensor"]:
        """Pad images using Torchvision with batched operations."""
        if pad_size is not None:
            if not (pad_size.height and pad_size.width):
                raise ValueError(f"Pad size must contain 'height' and 'width' keys only. Got pad_size={pad_size}.")
            pad_size = (pad_size.height, pad_size.width)
        else:
            pad_size = get_max_height_width(images)

        grouped_images, grouped_images_index = group_images_by_shape(
            images, disable_grouping=disable_grouping, is_nested=is_nested
        )
        processed_images_grouped = {}
        processed_masks_grouped = {}
        for shape, stacked_images in grouped_images.items():
            image_size = stacked_images.shape[-2:]
            padding_height = pad_size[0] - image_size[0]
            padding_width = pad_size[1] - image_size[1]
            if padding_height < 0 or padding_width < 0:
                raise ValueError(
                    f"Padding dimensions are negative. Please make sure that the `pad_size` is larger than the "
                    f"image size. Got pad_size={pad_size}, image_size={image_size}."
                )
            if image_size != pad_size:
                padding = (0, 0, padding_width, padding_height)
                stacked_images = tvF.pad(stacked_images, padding, fill=fill_value, padding_mode=padding_mode)
            processed_images_grouped[shape] = stacked_images

            if return_mask:
                stacked_masks = torch.zeros_like(stacked_images, dtype=torch.int64)[..., 0, :, :]
                stacked_masks[..., : image_size[0], : image_size[1]] = 1
                processed_masks_grouped[shape] = stacked_masks

        processed_images = reorder_images(processed_images_grouped, grouped_images_index, is_nested=is_nested)
        if return_mask:
            processed_masks = reorder_images(processed_masks_grouped, grouped_images_index, is_nested=is_nested)
            return processed_images, processed_masks

        return processed_images