def _preprocess_image(
        self,
        image: ImageInput,
        do_resize: bool | None = None,
        size: dict[str, int] | None = None,
        resample: PILImageResampling | None = None,
        do_center_crop: bool | None = None,
        crop_size: dict[str, int] | None = None,
        do_rescale: bool | None = None,
        rescale_factor: float | None = None,
        offset: bool | None = None,
        do_normalize: bool | None = None,
        image_mean: float | list[float] | None = None,
        image_std: float | list[float] | None = None,
        data_format: ChannelDimension | None = ChannelDimension.FIRST,
        input_data_format: str | ChannelDimension | None = None,
    ) -> np.ndarray:
        """Preprocesses a single image."""

        validate_preprocess_arguments(
            do_rescale=do_rescale,
            rescale_factor=rescale_factor,
            do_normalize=do_normalize,
            image_mean=image_mean,
            image_std=image_std,
            do_center_crop=do_center_crop,
            crop_size=crop_size,
            do_resize=do_resize,
            size=size,
            resample=resample,
        )

        if offset and not do_rescale:
            raise ValueError("For offset, do_rescale must also be set to True.")

        # All transformations expect numpy arrays.
        image = to_numpy_array(image)

        if do_rescale and is_scaled_image(image):
            logger.warning_once(
                "It looks like you are trying to rescale already rescaled images. If the input"
                " images have pixel values between 0 and 1, set `do_rescale=False` to avoid rescaling them again."
            )

        if input_data_format is None:
            input_data_format = infer_channel_dimension_format(image)

        if do_resize:
            image = self.resize(image=image, size=size, resample=resample, input_data_format=input_data_format)

        if do_center_crop:
            image = self.center_crop(image, size=crop_size, input_data_format=input_data_format)

        if do_rescale:
            image = self.rescale(image=image, scale=rescale_factor, offset=offset, input_data_format=input_data_format)

        if do_normalize:
            image = self.normalize(image=image, mean=image_mean, std=image_std, input_data_format=input_data_format)

        image = to_channel_dimension_format(image, data_format, input_channel_dim=input_data_format)
        return image