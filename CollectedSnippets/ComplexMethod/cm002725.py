def from_dict(cls, video_processor_dict: dict[str, Any], **kwargs):
        """
        Instantiates a type of [`~video_processing_utils.VideoProcessorBase`] from a Python dictionary of parameters.

        Args:
            video_processor_dict (`dict[str, Any]`):
                Dictionary that will be used to instantiate the video processor object. Such a dictionary can be
                retrieved from a pretrained checkpoint by leveraging the
                [`~video_processing_utils.VideoProcessorBase.to_dict`] method.
            kwargs (`dict[str, Any]`):
                Additional parameters from which to initialize the video processor object.

        Returns:
            [`~video_processing_utils.VideoProcessorBase`]: The video processor object instantiated from those
            parameters.
        """
        video_processor_dict = video_processor_dict.copy()
        return_unused_kwargs = kwargs.pop("return_unused_kwargs", False)
        video_processor_dict.update({k: v for k, v in kwargs.items() if k in cls.valid_kwargs.__annotations__})
        video_processor = cls(**video_processor_dict)

        # Apply extra kwargs to instance (BC for remote code, e.g. phi4_multimodal)
        extra_keys = []
        for key in reversed(list(kwargs.keys())):
            if hasattr(video_processor, key) and key not in cls.valid_kwargs.__annotations__:
                setattr(video_processor, key, kwargs.pop(key, None))
                extra_keys.append(key)
        if extra_keys:
            logger.warning_once(
                f"Image processor {cls.__name__}: kwargs {extra_keys} were applied for backward compatibility. "
                f"To avoid this warning, add them to valid_kwargs: create a custom TypedDict extending "
                f"ImagesKwargs with these keys and set it as the `valid_kwargs` class attribute."
            )

        logger.info(f"Video processor {video_processor}")
        if return_unused_kwargs:
            return video_processor, kwargs
        else:
            return video_processor