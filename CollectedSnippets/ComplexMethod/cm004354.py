def preprocess(
        self,
        videos: ImageInput,
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
        return_tensors: str | TensorType | None = None,
        data_format: ChannelDimension = ChannelDimension.FIRST,
        input_data_format: str | ChannelDimension | None = None,
    ) -> PIL.Image.Image:
        """
        Preprocess an image or batch of images.

        Args:
            videos (`ImageInput`):
                Video frames to preprocess. Expects a single or batch of video frames with pixel values ranging from 0
                to 255. If passing in frames with pixel values between 0 and 1, set `do_rescale=False`.
            do_resize (`bool`, *optional*, defaults to `self.do_resize`):
                Whether to resize the image.
            size (`dict[str, int]`, *optional*, defaults to `self.size`):
                Size of the image after applying resize.
            resample (`PILImageResampling`, *optional*, defaults to `self.resample`):
                Resampling filter to use if resizing the image. This can be one of the enum `PILImageResampling`, Only
                has an effect if `do_resize` is set to `True`.
            do_center_crop (`bool`, *optional*, defaults to `self.do_centre_crop`):
                Whether to centre crop the image.
            crop_size (`dict[str, int]`, *optional*, defaults to `self.crop_size`):
                Size of the image after applying the centre crop.
            do_rescale (`bool`, *optional*, defaults to `self.do_rescale`):
                Whether to rescale the image values between `[-1 - 1]` if `offset` is `True`, `[0, 1]` otherwise.
            rescale_factor (`float`, *optional*, defaults to `self.rescale_factor`):
                Rescale factor to rescale the image by if `do_rescale` is set to `True`.
            offset (`bool`, *optional*, defaults to `self.offset`):
                Whether to scale the image in both negative and positive directions.
            do_normalize (`bool`, *optional*, defaults to `self.do_normalize`):
                Whether to normalize the image.
            image_mean (`float` or `list[float]`, *optional*, defaults to `self.image_mean`):
                Image mean.
            image_std (`float` or `list[float]`, *optional*, defaults to `self.image_std`):
                Image standard deviation.
            return_tensors (`str` or `TensorType`, *optional*):
                The type of tensors to return. Can be one of:
                    - Unset: Return a list of `np.ndarray`.
                    - `TensorType.PYTORCH` or `'pt'`: Return a batch of type `torch.Tensor`.
                    - `TensorType.NUMPY` or `'np'`: Return a batch of type `np.ndarray`.
            data_format (`ChannelDimension` or `str`, *optional*, defaults to `ChannelDimension.FIRST`):
                The channel dimension format for the output image. Can be one of:
                    - `ChannelDimension.FIRST`: image in (num_channels, height, width) format.
                    - `ChannelDimension.LAST`: image in (height, width, num_channels) format.
                    - Unset: Use the inferred channel dimension format of the input image.
            input_data_format (`ChannelDimension` or `str`, *optional*):
                The channel dimension format for the input image. If unset, the channel dimension format is inferred
                from the input image. Can be one of:
                - `"channels_first"` or `ChannelDimension.FIRST`: image in (num_channels, height, width) format.
                - `"channels_last"` or `ChannelDimension.LAST`: image in (height, width, num_channels) format.
                - `"none"` or `ChannelDimension.NONE`: image in (height, width) format.
        """
        do_resize = do_resize if do_resize is not None else self.do_resize
        resample = resample if resample is not None else self.resample
        do_center_crop = do_center_crop if do_center_crop is not None else self.do_center_crop
        do_rescale = do_rescale if do_rescale is not None else self.do_rescale
        rescale_factor = rescale_factor if rescale_factor is not None else self.rescale_factor
        offset = offset if offset is not None else self.offset
        do_normalize = do_normalize if do_normalize is not None else self.do_normalize
        image_mean = image_mean if image_mean is not None else self.image_mean
        image_std = image_std if image_std is not None else self.image_std

        size = size if size is not None else self.size
        size = get_size_dict(size, default_to_square=False)
        crop_size = crop_size if crop_size is not None else self.crop_size
        crop_size = get_size_dict(crop_size, param_name="crop_size")

        if not valid_images(videos):
            raise ValueError("Invalid image type. Must be of type PIL.Image.Image, numpy.ndarray, or torch.Tensor")

        videos = make_batched(videos)

        videos = [
            [
                self._preprocess_image(
                    image=img,
                    do_resize=do_resize,
                    size=size,
                    resample=resample,
                    do_center_crop=do_center_crop,
                    crop_size=crop_size,
                    do_rescale=do_rescale,
                    rescale_factor=rescale_factor,
                    offset=offset,
                    do_normalize=do_normalize,
                    image_mean=image_mean,
                    image_std=image_std,
                    data_format=data_format,
                    input_data_format=input_data_format,
                )
                for img in video
            ]
            for video in videos
        ]

        data = {"pixel_values": videos}
        return BatchFeature(data=data, tensor_type=return_tensors)