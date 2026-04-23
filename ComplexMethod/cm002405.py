def process_image(
        self,
        image: ImageInput,
        do_convert_rgb: bool | None = None,
        input_data_format: str | ChannelDimension | None = None,
        **kwargs: Unpack[ImagesKwargs],
    ) -> np.ndarray:
        """Process a single image for PIL backend."""
        image_type = get_image_type(image)
        if image_type not in [ImageType.PIL, ImageType.TORCH, ImageType.NUMPY]:
            raise ValueError(f"Unsupported input image type {image_type}")

        if do_convert_rgb:
            image = self.convert_to_rgb(image)

        if image_type == ImageType.PIL:
            image = np.array(image)
            # Set LAST only for multi-channel PIL images (H, W, C); for grayscale (H, W), leave as is to avoid shape errors after expand_dims.
            if image.ndim >= 3:
                input_data_format = ChannelDimension.LAST if input_data_format is None else input_data_format
        elif image_type == ImageType.TORCH:
            image = image.numpy()

        if image.ndim == 2:
            image = np.expand_dims(image, axis=0)

        if input_data_format is None:
            input_data_format = infer_channel_dimension_format(image)

        if input_data_format == ChannelDimension.LAST:
            # Convert from channels-last to channels-first
            if isinstance(image, np.ndarray):
                image = np.transpose(image, (2, 0, 1))

        return image