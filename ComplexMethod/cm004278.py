def register(
        config_class,
        slow_image_processor_class: type | None = None,
        fast_image_processor_class: type | None = None,
        image_processor_classes: dict[str, type] | None = None,
        exist_ok: bool = False,
    ):
        """
        Register a new image processor for this class.

        Args:
            config_class ([`PreTrainedConfig`]):
                The configuration corresponding to the model to register.
            slow_image_processor_class (`type`, *optional*):
                The PIL backend image processor class (deprecated, use `image_processor_classes={"pil": ...}`).
            fast_image_processor_class (`type`, *optional*):
                The Torchvision backend image processor class (deprecated, use `image_processor_classes={"torchvision": ...}`).
            image_processor_classes (`dict[str, type]`, *optional*):
                Dictionary mapping backend names to image processor classes. Allows registering custom backends.
                Example: `{"pil": MyPilProcessor, "torchvision": MyTorchvisionProcessor, "custom": MyCustomProcessor}`
            exist_ok (`bool`, *optional*, defaults to `False`):
                If `True`, allow overwriting existing registrations.
        """
        # Handle backward compatibility: convert old parameters to new format
        if image_processor_classes is None:
            image_processor_classes = {}
            if slow_image_processor_class is not None:
                image_processor_classes["pil"] = slow_image_processor_class
            if fast_image_processor_class is not None:
                image_processor_classes["torchvision"] = fast_image_processor_class

        if not image_processor_classes:
            raise ValueError(
                "You need to specify at least one image processor class. "
                "Use `image_processor_classes={'backend_name': ProcessorClass}` or the deprecated "
                "`slow_image_processor_class`/`fast_image_processor_class` parameters."
            )

        # Avoid resetting existing processors if we are passing partial updates
        if config_class in IMAGE_PROCESSOR_MAPPING._extra_content:
            existing_mapping = IMAGE_PROCESSOR_MAPPING[config_class]
            existing_mapping.update(image_processor_classes)
            image_processor_classes = existing_mapping

        # Validate that all classes are proper image processor classes
        from ...image_processing_utils import BaseImageProcessor

        for backend_key, processor_class in image_processor_classes.items():
            if processor_class is not None and not issubclass(processor_class, BaseImageProcessor):
                raise ValueError(
                    f"Image processor class for backend '{backend_key}' must inherit from `BaseImageProcessor`. "
                    f"Got: {processor_class}"
                )
        IMAGE_PROCESSOR_MAPPING.register(config_class, image_processor_classes, exist_ok=exist_ok)