def pad(
        self, images: list[np.ndarray], return_pixel_mask: bool = True, return_tensors: str | TensorType | None = None
    ) -> BatchFeature:
        """
        Pad a batch of images to the same size using numpy operations.

        Args:
            images (`List[np.ndarray]`):
                List of image arrays in channel-first format.
            return_pixel_mask (`bool`, *optional*, defaults to `True`):
                Whether to return pixel masks.
            return_tensors (`str` or `TensorType`, *optional*):
                The type of tensors to return.

        Returns:
            `BatchFeature`: Padded images and optional pixel masks.
        """
        pad_size = get_max_height_width(images, input_data_format=ChannelDimension.FIRST)

        padded_images = []
        pixel_masks = []
        for image in images:
            padded_image = self._pad_image(image, pad_size, constant_values=0)
            padded_images.append(padded_image)
            if return_pixel_mask:
                pixel_mask = make_pixel_mask(image, pad_size)
                pixel_masks.append(pixel_mask)

        if return_tensors == "pt":
            padded_images = [torch.from_numpy(img) for img in padded_images]
            padded_images = torch.stack(padded_images, dim=0)
            if return_pixel_mask:
                pixel_masks = [torch.from_numpy(mask) for mask in pixel_masks]
                pixel_masks = torch.stack(pixel_masks, dim=0)

        data = {"pixel_values": padded_images}
        if return_pixel_mask:
            data["pixel_mask"] = pixel_masks

        return BatchFeature(data=data, tensor_type=return_tensors)