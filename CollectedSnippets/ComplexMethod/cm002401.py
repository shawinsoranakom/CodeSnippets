def process_image(
        self,
        image: ImageInput,
        do_convert_rgb: bool | None = None,
        input_data_format: str | ChannelDimension | None = None,
        device: Optional["torch.device"] = None,
        **kwargs: Unpack[ImagesKwargs],
    ) -> "torch.Tensor":
        """Process a single image for torchvision backend."""
        image_type = get_image_type(image)
        if image_type not in [ImageType.PIL, ImageType.TORCH, ImageType.NUMPY]:
            raise ValueError(f"Unsupported input image type {image_type}")

        if do_convert_rgb:
            image = self.convert_to_rgb(image)

        if image_type == ImageType.PIL:
            image = tvF.pil_to_tensor(image)
        elif image_type == ImageType.NUMPY:
            image = torch.from_numpy(image).contiguous()

        if image.ndim == 2:
            image = image.unsqueeze(0)

        if input_data_format is None:
            input_data_format = infer_channel_dimension_format(image)

        if input_data_format == ChannelDimension.LAST:
            image = image.permute(2, 0, 1).contiguous()

        if device is not None:
            image = image.to(device)

        return image