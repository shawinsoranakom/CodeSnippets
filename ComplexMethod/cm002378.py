def get_processor_types_from_config_class(config_class, allowed_mappings=None):
    """Return a tuple of processors for `config_class`.

    We use `tuple` here to include (potentially) both slow & fast tokenizers.
    """

    # To make a uniform return type
    def _to_tuple(x):
        if isinstance(x, dict):
            x = tuple(x.values())
        elif not isinstance(x, collections.abc.Sequence):
            x = (x,)
        else:
            x = tuple(x)
        return x

    if allowed_mappings is None:
        allowed_mappings = ["processor", "tokenizer", "image_processor", "feature_extractor"]

    processor_types = ()

    # Check first if a model has `ProcessorMixin`. Otherwise, check if it has tokenizers, and/or an image processor or
    # a feature extractor
    if config_class in PROCESSOR_MAPPING and "processor" in allowed_mappings:
        processor_types = _to_tuple(PROCESSOR_MAPPING[config_class])
    else:
        if config_class in TOKENIZER_MAPPING and "tokenizer" in allowed_mappings:
            processor_types = _to_tuple(TOKENIZER_MAPPING[config_class])

        if config_class in IMAGE_PROCESSOR_MAPPING and "image_processor" in allowed_mappings:
            processor_types += _to_tuple(IMAGE_PROCESSOR_MAPPING[config_class])
        elif config_class in FEATURE_EXTRACTOR_MAPPING and "feature_extractor" in allowed_mappings:
            processor_types += _to_tuple(FEATURE_EXTRACTOR_MAPPING[config_class])

    # Remark: some configurations have no processor at all. For example, generic composite models like
    # `EncoderDecoderModel` is used for any (compatible) text models. Also, `DecisionTransformer` doesn't
    # require any processor.

    # We might get `None` for some tokenizers - remove them here.
    processor_types = tuple(p for p in processor_types if p is not None)

    # Add what ever auto types
    processor_types += (AutoTokenizer, AutoImageProcessor, AutoFeatureExtractor, AutoVideoProcessor)

    # TODO: Make this better and clean
    # The repository `microsoft/VibeVoice-1.5B` has `model_type="vibevoice"` which doesn't exist, and the `preprocessor_config.json`
    # contains `VibeVoiceTokenizerProcessor` and `VibeVoiceProcessor` also don't exist.
    # The feature extractor auto mapping only has entries for `vibevoice_acoustic_tokenizer` but not for encoder/decoder config.
    if config_class.__name__ in ["VibeVoiceAcousticTokenizerEncoderConfig", "VibeVoiceAcousticTokenizerDecoderConfig"]:
        processor_types = (VibeVoiceAcousticTokenizerFeatureExtractor,) + processor_types

    return processor_types