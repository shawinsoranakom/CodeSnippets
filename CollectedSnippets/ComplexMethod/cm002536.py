def get_possibly_dynamic_module(module_name):
        if hasattr(transformers_module, module_name):
            return getattr(transformers_module, module_name)
        lookup_locations = [
            transformers_module.IMAGE_PROCESSOR_MAPPING,
            transformers_module.VIDEO_PROCESSOR_MAPPING,
            transformers_module.TOKENIZER_MAPPING,
            transformers_module.FEATURE_EXTRACTOR_MAPPING,
            transformers_module.MODEL_FOR_AUDIO_TOKENIZATION_MAPPING,
        ]
        for lookup_location in lookup_locations:
            for custom_class in lookup_location._extra_content.values():
                if isinstance(custom_class, tuple):
                    for custom_subclass in custom_class:
                        if custom_subclass is not None and custom_subclass.__name__ == module_name:
                            return custom_subclass
                elif custom_class is not None and custom_class.__name__ == module_name:
                    return custom_class
        raise ValueError(
            f"Could not find module {module_name} in `transformers`. If this is a custom class, "
            f"it should be registered using the relevant `AutoClass.register()` function so that "
            f"other functions can find it!"
        )