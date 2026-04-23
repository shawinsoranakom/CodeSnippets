def convert_processors(processors, tiny_config, output_folder, result):
    """Change a processor to work with smaller inputs.

    For tokenizers, we try to reduce their vocabulary size.

    For feature extractor, we use smaller image size or change
    other attributes using the values from `tiny_config`. See `convert_feature_extractor`.

    This method should not fail: we catch the errors and put them in `result["warnings"]` with descriptive messages.
    """

    def _sanity_check(fast_tokenizer, slow_tokenizer, keep_fast_tokenizer=False):
        """Set tokenizer(s) to `None` if the fast/slow tokenizers have different values for `vocab_size` or `length`.

        If `keep_fast_tokenizer=True`, the fast tokenizer will be kept.
        """
        # sanity check 1: fast and slow tokenizers should be compatible (vocab_size)
        if fast_tokenizer is not None and slow_tokenizer is not None:
            if fast_tokenizer.vocab_size != slow_tokenizer.vocab_size:
                warning_message = (
                    "The fast/slow tokenizers "
                    f"({fast_tokenizer.__class__.__name__}/{slow_tokenizer.__class__.__name__}) have different "
                    "vocabulary size: "
                    f"fast_tokenizer.vocab_size = {fast_tokenizer.vocab_size} and "
                    f"slow_tokenizer.vocab_size = {slow_tokenizer.vocab_size}."
                )
                result["warnings"].append(warning_message)
                if not keep_fast_tokenizer:
                    fast_tokenizer = None
                slow_tokenizer = None

        # sanity check 2: fast and slow tokenizers should be compatible (length)
        if fast_tokenizer is not None and slow_tokenizer is not None:
            if len(fast_tokenizer) != len(slow_tokenizer):
                warning_message = (
                    f"The fast/slow tokenizers () have different length: "
                    f"len(fast_tokenizer) = {len(fast_tokenizer)} and "
                    f"len(slow_tokenizer) = {len(slow_tokenizer)}."
                )
                result["warnings"].append(warning_message)
                if not keep_fast_tokenizer:
                    fast_tokenizer = None
                slow_tokenizer = None

        return fast_tokenizer, slow_tokenizer

    tokenizers = []
    feature_extractors = []
    for processor in processors:
        if isinstance(processor, PreTrainedTokenizerBase):
            if processor.__class__.__name__ not in {x.__class__.__name__ for x in tokenizers}:
                tokenizers.append(processor)
        elif isinstance(processor, BaseImageProcessor):
            if processor.__class__.__name__ not in {x.__class__.__name__ for x in feature_extractors}:
                feature_extractors.append(processor)
        elif isinstance(processor, FeatureExtractionMixin):
            if processor.__class__.__name__ not in {x.__class__.__name__ for x in feature_extractors}:
                feature_extractors.append(processor)
        elif isinstance(processor, ProcessorMixin):
            if hasattr(processor, "tokenizer"):
                if processor.tokenizer.__class__.__name__ not in {x.__class__.__name__ for x in tokenizers}:
                    tokenizers.append(processor.tokenizer)
            # Currently, we only have these 2 possibilities
            if hasattr(processor, "image_processor"):
                if processor.image_processor.__class__.__name__ not in {
                    x.__class__.__name__ for x in feature_extractors
                }:
                    feature_extractors.append(processor.image_processor)
            elif hasattr(processor, "feature_extractor"):
                if processor.feature_extractor.__class__.__name__ not in {
                    x.__class__.__name__ for x in feature_extractors
                }:
                    feature_extractors.append(processor.feature_extractor)

    # check the built processors have the unique type
    len({x.__class__.__name__ for x in feature_extractors})
    # if num_types >= 2:
    #     raise ValueError(f"`feature_extractors` should contain at most 1 type, but it contains {num_types} types!")
    len({x.__class__.__name__.replace("Fast", "") for x in tokenizers})

    # TODO: we might have {'TokenizersBackend', 'MistralCommonBackend'} now! For example, mixtral!
    # TODO: Question: if we need to have "tokenizer.model" or "special_tokens_map.json"?
    # if num_types >= 2:
    #     raise ValueError(f"`tokenizers` should contain at most 1 tokenizer type, but it contains {num_types} types!")

    fast_tokenizer = None
    slow_tokenizer = None

    for tokenizer in tokenizers:
        if isinstance(tokenizer, PreTrainedTokenizerFast):
            fast_tokenizer = tokenizer
        else:
            slow_tokenizer = tokenizer

    # If the (original) fast/slow tokenizers don't correspond, keep only the fast tokenizer.
    # This doesn't necessarily imply the fast/slow tokenizers in a single Hub repo. has issues.
    # It's more of an issue in `build_processor` which tries to get a checkpoint with as much effort as possible.
    # For `YosoModel` (which uses `AlbertTokenizer(Fast)`), its real (Hub) checkpoint doesn't contain valid files to
    # load the slower tokenizer (`AlbertTokenizer`), and it ends up finding the (canonical) checkpoint of `AlbertModel`,
    # which has different vocabulary.
    # TODO: Try to improve `build_processor`'s definition and/or usage to avoid the above situation in the first place.
    fast_tokenizer, slow_tokenizer = _sanity_check(fast_tokenizer, slow_tokenizer, keep_fast_tokenizer=True)
    original_fast_tokenizer, original_slow_tokenizer = fast_tokenizer, slow_tokenizer

    if fast_tokenizer:
        try:
            # Wav2Vec2ForCTC , ByT5Tokenizer etc. all are already small enough and have no fast version that can
            # be retrained
            if fast_tokenizer.vocab_size > TARGET_VOCAB_SIZE:
                pass
                # fast_tokenizer = convert_tokenizer(fast_tokenizer)
        except Exception:
            result["warnings"].append(
                (
                    f"Failed to convert the fast tokenizer for {fast_tokenizer.__class__.__name__}.",
                    traceback.format_exc(),
                )
            )

    # If `fast_tokenizer` exists, `slow_tokenizer` should correspond to it.
    if fast_tokenizer:
        # Make sure the fast tokenizer can be saved
        try:
            # We don't save it to `output_folder` at this moment - only at the end of this function.
            with tempfile.TemporaryDirectory() as tmpdir:
                fast_tokenizer.save_pretrained(tmpdir)
                try:
                    slow_tokenizer = AutoTokenizer.from_pretrained(tmpdir, use_fast=False)
                except Exception:
                    result["warnings"].append(
                        (
                            f"Failed to load the slow tokenizer saved from {fast_tokenizer.__class__.__name__}.",
                            traceback.format_exc(),
                        )
                    )
                    # Let's just keep the fast version
                    slow_tokenizer = None
        except Exception:
            result["warnings"].append(
                (
                    f"Failed to save the fast tokenizer for {fast_tokenizer.__class__.__name__}.",
                    traceback.format_exc(),
                )
            )
            fast_tokenizer = None

    # If the (possibly converted) fast/slow tokenizers don't correspond, set them to `None`, and use the original
    # tokenizers.
    fast_tokenizer, slow_tokenizer = _sanity_check(fast_tokenizer, slow_tokenizer, keep_fast_tokenizer=False)

    # If there is any conversion failed, we keep the original tokenizers.
    if (original_fast_tokenizer is not None and fast_tokenizer is None) or (
        original_slow_tokenizer is not None and slow_tokenizer is None
    ):
        warning_messagae = (
            "There are some issues when converting the fast/slow tokenizers. The original tokenizers from the Hub "
            " will be used instead."
        )
        result["warnings"].append(warning_messagae)
        # Let's use the original version at the end (`original_fast_tokenizer` and `original_slow_tokenizer`)
        fast_tokenizer = original_fast_tokenizer
        slow_tokenizer = original_slow_tokenizer

    # Make sure the fast tokenizer can be saved
    if fast_tokenizer:
        # We don't save it to `output_folder` at this moment - only at the end of this function.
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                fast_tokenizer.save_pretrained(tmpdir)
            except Exception:
                result["warnings"].append(
                    (
                        f"Failed to save the fast tokenizer for {fast_tokenizer.__class__.__name__}.",
                        traceback.format_exc(),
                    )
                )
                fast_tokenizer = None
    # Make sure the slow tokenizer can be saved
    if slow_tokenizer:
        # We don't save it to `output_folder` at this moment - only at the end of this function.
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                slow_tokenizer.save_pretrained(tmpdir)
            except Exception:
                result["warnings"].append(
                    (
                        f"Failed to save the slow tokenizer for {slow_tokenizer.__class__.__name__}.",
                        traceback.format_exc(),
                    )
                )
                slow_tokenizer = None

    # update feature extractors using the tiny config
    try:
        feature_extractors = [convert_feature_extractor(p, tiny_config) for p in feature_extractors]
    except Exception:
        result["warnings"].append(
            (
                "Failed to convert feature extractors.",
                traceback.format_exc(),
            )
        )
        feature_extractors = []

    if hasattr(tiny_config, "max_position_embeddings") and tiny_config.max_position_embeddings > 0:
        if fast_tokenizer is not None:
            if fast_tokenizer.__class__.__name__ in [
                "RobertaTokenizerFast",
                "XLMRobertaTokenizerFast",
                "LongformerTokenizerFast",
                "MPNetTokenizerFast",
            ]:
                fast_tokenizer.model_max_length = tiny_config.max_position_embeddings - 2
            else:
                fast_tokenizer.model_max_length = tiny_config.max_position_embeddings
        if slow_tokenizer is not None:
            if slow_tokenizer.__class__.__name__ in [
                "RobertaTokenizer",
                "XLMRobertaTokenizer",
                "LongformerTokenizer",
                "MPNetTokenizer",
            ]:
                slow_tokenizer.model_max_length = tiny_config.max_position_embeddings - 2
            else:
                slow_tokenizer.model_max_length = tiny_config.max_position_embeddings

    processors = [fast_tokenizer, slow_tokenizer] + feature_extractors
    processors = [p for p in processors if p is not None]
    for p in processors:
        p.save_pretrained(output_folder)

    return processors