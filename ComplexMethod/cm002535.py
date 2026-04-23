def _get_arguments_from_pretrained(cls, pretrained_model_name_or_path, processor_dict=None, **kwargs):
        """
        Identify and instantiate the subcomponents of Processor classes, such as image processors, tokenizers,
        and feature extractors. This method inspects the processor's `__init__` signature to identify parameters
        that correspond to known modality types (image_processor, tokenizer, feature_extractor, etc.) or contain
        modality names in their attribute name.

        For tokenizers: Uses the appropriate Auto class (AutoTokenizer) to load via `.from_pretrained()`.
        Additional tokenizers (e.g., "decoder_tokenizer") are loaded from subfolders.

        For other sub-processors (image_processor, feature_extractor, etc.): Primary ones are loaded via
        Auto class. Additional ones are instantiated from the config stored in processor_config.json
        (passed as processor_dict).

        Args:
            pretrained_model_name_or_path: Path or model id to load from.
            processor_dict: Optional dict containing processor config (from processor_config.json).
                Required when loading additional non-tokenizer sub-processors.
        """
        args = []
        processor_dict = processor_dict if processor_dict is not None else {}
        # Remove subfolder from kwargs to avoid duplicate keyword arguments
        subfolder = kwargs.pop("subfolder", "")

        # get args from processor init signature
        sub_processors = cls.get_attributes()
        for sub_processor_type in sub_processors:
            modality = _get_modality_for_attribute(sub_processor_type)
            is_primary = sub_processor_type == modality

            if (
                "tokenizer" in sub_processor_type
            ):  # This is only necessary for the checkpoint in test_processing_mistral3.py which has no config.json and
                # the tokenizer_config.json references LlamaTokenizerFast. TODO: update the config on the hub.
                if "PixtralProcessor" in cls.__name__:
                    from .tokenization_utils_tokenizers import TokenizersBackend

                    tokenizer = TokenizersBackend.from_pretrained(
                        pretrained_model_name_or_path, subfolder=subfolder, **kwargs
                    )
                else:
                    tokenizer = cls._load_tokenizer_from_pretrained(
                        sub_processor_type, pretrained_model_name_or_path, subfolder=subfolder, **kwargs
                    )
                args.append(tokenizer)
            elif is_primary:
                # Primary non-tokenizer sub-processor: load via Auto class
                auto_processor_class = MODALITY_TO_AUTOPROCESSOR_MAPPING[sub_processor_type]
                # For backward compatibility, check if sub-processor class name is hardcoded as an attribute of the processor class.
                if hasattr(cls, sub_processor_type + "_class"):
                    sub_processor_class_name = getattr(cls, sub_processor_type + "_class")
                    logger.warning_once(
                        f"`{cls.__name__}` defines `{sub_processor_type}_class = '{sub_processor_class_name}'`, "
                        f"which is deprecated. Register the correct mapping in `{auto_processor_class.__name__}` instead.",
                    )
                    auto_processor_class = cls.get_possibly_dynamic_module(sub_processor_class_name)
                sub_processor = auto_processor_class.from_pretrained(
                    pretrained_model_name_or_path, subfolder=subfolder, **kwargs
                )
                args.append(sub_processor)

            elif sub_processor_type in processor_dict:
                # Additional non-tokenizer sub-processor: instantiate from config in processor_dict
                sub_processor_config = processor_dict[sub_processor_type]
                if isinstance(sub_processor_config, dict):
                    # Determine the class to instantiate
                    # Image processors have 'image_processor_type', feature extractors have 'feature_extractor_type'
                    type_key = f"{modality}_type"
                    class_name = sub_processor_config.get(type_key)
                    if class_name is None:
                        raise ValueError(
                            f"Cannot instantiate {sub_processor_type}: missing '{type_key}' in config. "
                            f"Config keys: {list(sub_processor_config.keys())}"
                        )
                    processor_class = cls.get_possibly_dynamic_module(class_name)
                    sub_processor = processor_class(**sub_processor_config)
                    args.append(sub_processor)
                else:
                    raise ValueError(
                        f"Expected dict for {sub_processor_type} in processor_config.json, "
                        f"got {type(sub_processor_config)}"
                    )
            else:
                raise ValueError(
                    f"Cannot find config for {sub_processor_type} in processor_config.json. "
                    f"Available keys: {list(processor_dict.keys())}"
                )

        return args