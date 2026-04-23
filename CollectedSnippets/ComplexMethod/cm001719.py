def resolve_model_type_to_attribute(model_type, mapping_name):
        from transformers.models.auto.configuration_auto import CONFIG_MAPPING

        config_class = CONFIG_MAPPING[model_type]

        # Get the appropriate Auto mapping for this component type
        if mapping_name == "tokenizer":
            from transformers.models.auto.tokenization_auto import TOKENIZER_MAPPING
            from transformers.utils import is_tokenizers_available

            component_class = TOKENIZER_MAPPING.get(config_class, None)
            if component_class is None and is_tokenizers_available():
                from transformers.tokenization_utils_tokenizers import TokenizersBackend

                component_class = TokenizersBackend
        elif mapping_name == "image_processor":
            from transformers.models.auto.image_processing_auto import IMAGE_PROCESSOR_MAPPING

            component_class = IMAGE_PROCESSOR_MAPPING.get(config_class, None)
        elif mapping_name == "feature_extractor" or mapping_name == "audio_processor":
            from transformers.models.auto.feature_extraction_auto import FEATURE_EXTRACTOR_MAPPING

            component_class = FEATURE_EXTRACTOR_MAPPING.get(config_class, None)
        elif mapping_name == "video_processor":
            from transformers.models.auto.video_processing_auto import VIDEO_PROCESSOR_MAPPING

            component_class = VIDEO_PROCESSOR_MAPPING.get(config_class, None)
        else:
            raise ValueError(f"Unknown mapping for attribute: {mapping_name}")
        return component_class