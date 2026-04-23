def get_image_processor_class_from_name(class_name: str):
    """Resolve an image processor class name to its class. Handles both base names (e.g. CLIPImageProcessor)
    and PIL backend names (e.g. CLIPImageProcessorPil). No recursion needed since names are direct."""
    if class_name == "BaseImageProcessorFast":
        # kept for backward compatibility - return TorchvisionBackend
        from ...image_processing_backends import TorchvisionBackend

        return TorchvisionBackend

    # First, check registered extra content (user-registered classes)
    for mapping in IMAGE_PROCESSOR_MAPPING._extra_content.values():
        for extractor_class in mapping.values():
            if isinstance(extractor_class, type) and getattr(extractor_class, "__name__", None) == class_name:
                return extractor_class

    # Check the mapping names - class names are either base (torchvision) or base+Pil (pil)
    for model_type, extractors_dict in IMAGE_PROCESSOR_MAPPING_NAMES.items():
        if class_name in extractors_dict.values():
            module_name = model_type_to_module_name(model_type)
            module = importlib.import_module(f".{module_name}", "transformers.models")
            try:
                return getattr(module, class_name)
            except AttributeError:
                continue

    # Fallback: class may be in main init (e.g. when dep is missing, returns dummy)
    main_module = importlib.import_module("transformers")
    if hasattr(main_module, class_name):
        return getattr(main_module, class_name)

    return None