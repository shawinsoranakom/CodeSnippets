def preprocess(
        self,
        images: ImageInput,
        videos: VideoInput = None,
        do_resize: bool | None = None,
        size: dict[str, int] | None = None,
        min_pixels: int | None = None,
        max_pixels: int | None = None,
        resample: PILImageResampling = None,
        do_rescale: bool | None = None,
        rescale_factor: float | None = None,
        do_normalize: bool | None = None,
        image_mean: float | list[float] | None = None,
        image_std: float | list[float] | None = None,
        patch_size: int | None = None,
        temporal_patch_size: int | None = None,
        merge_size: int | None = None,
        do_convert_rgb: bool | None = None,
        return_tensors: str | TensorType | None = None,
        data_format: ChannelDimension | None = ChannelDimension.FIRST,
        input_data_format: str | ChannelDimension | None = None,
    ):
        """
        Args:
            images (`ImageInput`):
                Image to preprocess. Expects a single or batch of images with pixel values ranging from 0 to 255. If
                passing in images with pixel values between 0 and 1, set `do_rescale=False`.
            videos (`VideoInput`):
                Video to preprocess. Expects a single or batch of videos with pixel values ranging from 0 to 255. If
                passing in videos with pixel values between 0 and 1, set `do_rescale=False`.
            do_resize (`bool`, *optional*, defaults to `self.do_resize`):
                Whether to resize the image.
            size (`dict[str, int]`, *optional*, defaults to `self.size`):
                Size of the image after resizing. Shortest edge of the image is resized to size["shortest_edge"], with
                the longest edge resized to keep the input aspect ratio.
            resample (`int`, *optional*, defaults to `self.resample`):
                Resampling filter to use if resizing the image. This can be one of the enum `PILImageResampling`. Only
                has an effect if `do_resize` is set to `True`.
            do_rescale (`bool`, *optional*, defaults to `self.do_rescale`):
                Whether to rescale the image.
            rescale_factor (`float`, *optional*, defaults to `self.rescale_factor`):
                Rescale factor to rescale the image by if `do_rescale` is set to `True`.
            do_normalize (`bool`, *optional*, defaults to `self.do_normalize`):
                Whether to normalize the image.
            image_mean (`float` or `list[float]`, *optional*, defaults to `self.image_mean`):
                Image mean to use for normalization. Only has an effect if `do_normalize` is set to `True`.
            image_std (`float` or `list[float]`, *optional*, defaults to `self.image_std`):
                Image standard deviation to use for normalization. Only has an effect if `do_normalize` is set to
                `True`.
            min_pixels (`int`, *optional*, defaults to `self.min_pixels`):
                The min pixels of the image to resize the image.
            max_pixels (`int`, *optional*, defaults to `self.max_pixels`):
                The max pixels of the image to resize the image.
            patch_size (`int`, *optional*, defaults to `self.patch_size`):
                The spatial patch size of the vision encoder.
            temporal_patch_size (`int`, *optional*, defaults to `self.temporal_patch_size`):
                The temporal patch size of the vision encoder.
            merge_size (`int`, *optional*, defaults to `self.merge_size`):
                The merge size of the vision encoder to llm encoder.
            do_convert_rgb (`bool`, *optional*, defaults to `self.do_convert_rgb`):
                Whether to convert the image to RGB.
            return_tensors (`str` or `TensorType`, *optional*):
                The type of tensors to return. Can be one of:
                - Unset: Return a list of `np.ndarray`.
                - `TensorType.TENSORFLOW` or `'tf'`: Return a batch of type `tf.Tensor`.
                - `TensorType.PYTORCH` or `'pt'`: Return a batch of type `torch.Tensor`.
                - `TensorType.NUMPY` or `'np'`: Return a batch of type `np.ndarray`.
                - `TensorType.JAX` or `'jax'`: Return a batch of type `jax.numpy.ndarray`.
            data_format (`ChannelDimension` or `str`, *optional*, defaults to `ChannelDimension.FIRST`):
                The channel dimension format for the output image. Can be one of:
                - `"channels_first"` or `ChannelDimension.FIRST`: image in (num_channels, height, width) format.
                - `"channels_last"` or `ChannelDimension.LAST`: image in (height, width, num_channels) format.
                - Unset: Use the channel dimension format of the input image.
            input_data_format (`ChannelDimension` or `str`, *optional*):
                The channel dimension format for the input image. If unset, the channel dimension format is inferred
                from the input image. Can be one of:
                - `"channels_first"` or `ChannelDimension.FIRST`: image in (num_channels, height, width) format.
                - `"channels_last"` or `ChannelDimension.LAST`: image in (height, width, num_channels) format.
                - `"none"` or `ChannelDimension.NONE`: image in (height, width) format.

        """  # noqa: E501
        min_pixels = min_pixels if min_pixels is not None else self.min_pixels
        max_pixels = max_pixels if max_pixels is not None else self.max_pixels

        if size is not None:
            if "shortest_edge" not in size or "longest_edge" not in size:
                raise ValueError(
                    "size must contain 'shortest_edge' and 'longest_edge' keys."
                )
            min_pixels = size["shortest_edge"]
        elif min_pixels is not None and max_pixels is not None:
            # backward compatibility: override size with min_pixels and max_pixels
            # if they are provided.
            size = {"shortest_edge": min_pixels, "longest_edge": max_pixels}
        else:
            size = {**self.size}

        do_resize = do_resize if do_resize is not None else self.do_resize

        resample = resample if resample is not None else self.resample
        do_rescale = do_rescale if do_rescale is not None else self.do_rescale
        rescale_factor = (
            rescale_factor if rescale_factor is not None else self.rescale_factor
        )
        do_normalize = do_normalize if do_normalize is not None else self.do_normalize
        image_mean = image_mean if image_mean is not None else self.image_mean
        image_std = image_std if image_std is not None else self.image_std
        patch_size = patch_size if patch_size is not None else self.patch_size
        temporal_patch_size = (
            temporal_patch_size
            if temporal_patch_size is not None
            else self.temporal_patch_size
        )
        merge_size = merge_size if merge_size is not None else self.merge_size
        do_convert_rgb = (
            do_convert_rgb if do_convert_rgb is not None else self.do_convert_rgb
        )

        if images is not None:
            images = make_flat_list_of_images(images)

        if images is not None and not valid_images(images):
            raise ValueError(
                "Invalid image type. Must be of type PIL.Image.Image, numpy.ndarray, "
                "torch.Tensor, tf.Tensor or jax.ndarray."
            )

        validate_preprocess_arguments(
            rescale_factor=rescale_factor,
            do_normalize=do_normalize,
            image_mean=image_mean,
            image_std=image_std,
            do_resize=do_resize,
            size=size,
            resample=resample,
        )

        data = {}
        if images is not None:
            pixel_values, vision_grid_thws = [], []
            for image in images:
                patches, image_grid_thw = self._preprocess(
                    image,
                    do_resize=do_resize,
                    size=size,
                    resample=resample,
                    do_rescale=do_rescale,
                    rescale_factor=rescale_factor,
                    do_normalize=do_normalize,
                    image_mean=image_mean,
                    image_std=image_std,
                    patch_size=patch_size,
                    temporal_patch_size=temporal_patch_size,
                    merge_size=merge_size,
                    data_format=data_format,
                    do_convert_rgb=do_convert_rgb,
                    input_data_format=input_data_format,
                )
                pixel_values.extend(patches)
                vision_grid_thws.append(image_grid_thw)
            pixel_values = np.array(pixel_values)
            vision_grid_thws = np.array(vision_grid_thws)
            data.update(
                {"pixel_values": pixel_values, "image_grid_thw": vision_grid_thws}
            )

        # kept for BC only and should be removed after v5.0
        if videos is not None:
            logger.warning(
                "`HunYuanVLV1ImageProcessor` works only with image inputs "
                "and doesn't process videos anymore. "
                "This is a deprecated behavior and will be removed in v5.0. "
                "Your videos should be forwarded to `HunYuanVLV1VideoProcessor`. "
            )
            videos = make_batched_videos(videos)
            pixel_values_videos, vision_grid_thws_videos = [], []
            for images in videos:
                patches, video_grid_thw = self._preprocess(
                    images,
                    do_resize=do_resize,
                    size=size,
                    resample=resample,
                    do_rescale=do_rescale,
                    rescale_factor=rescale_factor,
                    do_normalize=do_normalize,
                    image_mean=image_mean,
                    image_std=image_std,
                    patch_size=patch_size,
                    temporal_patch_size=temporal_patch_size,
                    merge_size=merge_size,
                    data_format=data_format,
                    do_convert_rgb=do_convert_rgb,
                    input_data_format=input_data_format,
                )
                pixel_values_videos.extend(patches)
                vision_grid_thws_videos.append(video_grid_thw)
            data.update(
                {
                    "pixel_values_videos": np.array(pixel_values_videos),
                    "video_grid_thw": np.array(vision_grid_thws_videos),
                }
            )

        return BatchFeature(data=data, tensor_type=return_tensors)