def from_dict(cls, image_processor_dict: dict[str, Any], **kwargs):
        """
        Instantiates a type of [`~image_processing_utils.ImageProcessingMixin`] from a Python dictionary of parameters.

        Args:
            image_processor_dict (`dict[str, Any]`):
                Dictionary that will be used to instantiate the image processor object. Such a dictionary can be
                retrieved from a pretrained checkpoint by leveraging the
                [`~image_processing_utils.ImageProcessingMixin.to_dict`] method.
            kwargs (`dict[str, Any]`):
                Additional parameters from which to initialize the image processor object.

        Returns:
            [`~image_processing_utils.ImageProcessingMixin`]: The image processor object instantiated from those
            parameters.
        """
        image_processor_dict = image_processor_dict.copy()
        return_unused_kwargs = kwargs.pop("return_unused_kwargs", False)
        image_processor_dict.update({k: v for k, v in kwargs.items() if k in cls.valid_kwargs.__annotations__})
        image_processor = cls(**image_processor_dict)

        # Apply extra kwargs to instance (BC for remote code, e.g. phi4_multimodal)
        extra_keys = []
        for key in reversed(list(kwargs.keys())):
            if hasattr(image_processor, key) and key not in cls.valid_kwargs.__annotations__:
                setattr(image_processor, key, kwargs.pop(key, None))
                extra_keys.append(key)
        if extra_keys:
            logger.warning_once(
                f"Image processor {cls.__name__}: kwargs {extra_keys} were applied for backward compatibility. "
                f"To avoid this warning, add them to valid_kwargs: create a custom TypedDict extending "
                f"ImagesKwargs with these keys and set it as the `valid_kwargs` class attribute."
            )

        logger.info(f"Image processor {image_processor}")
        if return_unused_kwargs:
            return image_processor, kwargs
        else:
            return image_processor