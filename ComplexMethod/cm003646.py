def postprocess(
        self,
        images: ImageInput,
        do_rescale: bool | None = None,
        rescale_factor: float | None = None,
        do_normalize: bool | None = None,
        image_mean: float | list[float] | None = None,
        image_std: float | list[float] | None = None,
        return_tensors: str | TensorType = "PIL.Image.Image",
        input_data_format: str | ChannelDimension | None = None,
    ):
        """
        Postprocess an image or batch of images tensor. Postprocess is the reverse process of preprocess.
        The parameters should be same as in preprocess.
        Args:
            images (`ImageInput`):
                Image to postprocess. Expects a single or batch of images with pixel values ranging from -1 to 1.
            do_rescale (`bool`, *optional*, defaults to `self.do_rescale`):
                Whether to rescale the image.
            rescale_factor (`float`, *optional*, defaults to `self.rescale_factor`):
                Rescale factor to rescale the image by if `do_rescale` is set to `True`.
            do_normalize (`bool`, *optional*, defaults to `self.do_normalize`):
                Whether to normalize the image.
            image_mean (`float` or `list[float]`, *optional*, defaults to `self.image_mean`):
                Image mean to use for normalization. Only has an effect if `do_normalize` is set to `True`.
            image_std (`float` or `list[float]`, *optional*, defaults to `self.image_std`):
                Image standard deviation to use for normalization. Only has an effect if `do_normalize` is set to `True`.
            return_tensors (`str` or `TensorType`, *optional*):
                The type of tensors to return. Can be one of:
                - Unset: Return a list of `np.ndarray`.
                - `TensorType.PYTORCH` or `'pt'`: Return a batch of type `torch.Tensor`.
                - `TensorType.NUMPY` or `'np'`: Return a batch of type `np.ndarray`.
            input_data_format (`ChannelDimension` or `str`, *optional*):
                The channel dimension format for the input image. If unset, the channel dimension format is inferred
                from the input image. Can be one of:
                - `"channels_first"` or `ChannelDimension.FIRST`: image in (num_channels, height, width) format.
                - `"channels_last"` or `ChannelDimension.LAST`: image in (height, width, num_channels) format.
                - `"none"` or `ChannelDimension.NONE`: image in (height, width) format.
        """
        do_rescale = do_rescale if do_rescale is not None else self.do_rescale
        rescale_factor = 1.0 / self.rescale_factor if rescale_factor is None else rescale_factor
        do_normalize = do_normalize if do_normalize is not None else self.do_normalize
        image_mean = image_mean if image_mean is not None else self.image_mean
        image_std = image_std if image_std is not None else self.image_std

        images = make_flat_list_of_images(images)
        if isinstance(images[0], Image.Image):
            return images if len(images) > 1 else images[0]

        if input_data_format is None:
            # We assume that all images have the same channel dimension format.
            input_data_format = infer_channel_dimension_format(images[0])

        pixel_values = []
        for image in images:
            image = to_numpy_array(image)
            if do_normalize:
                image = self.unnormalize(
                    image=image, image_mean=image_mean, image_std=image_std, input_data_format=input_data_format
                )

            if do_rescale:
                image = self.rescale(image, scale=rescale_factor, input_data_format=input_data_format)
                image = image.clip(0, 255).astype(np.uint8)

            if do_normalize and do_rescale and return_tensors == "PIL.Image.Image":
                image = to_channel_dimension_format(image, ChannelDimension.LAST, input_channel_dim=input_data_format)
                pixel_values.append(Image.fromarray(image))
            else:
                pixel_values.extend(image)

        data = {"pixel_values": pixel_values}
        return_tensors = return_tensors if return_tensors != "PIL.Image.Image" else None

        return BatchFeature(data=data, tensor_type=return_tensors)