def build_processor(config_class, processor_class, allow_no_checkpoint=False):
    """Create a processor for `processor_class`.

    If a processor is not able to be built with the original arguments, this method tries to change the arguments and
    call itself recursively, by inferring a new `config_class` or a new `processor_class` from another one, in order to
    find a checkpoint containing the necessary files to build a processor.

    The processor is not saved here. Instead, it will be saved in `convert_processors` after further changes in
    `convert_processors`. For each model architecture`, a copy will be created and saved along the built model.
    """
    # Currently, this solely uses the docstring in the source file of `config_class` to find a checkpoint.
    checkpoint = get_checkpoint_from_config_class(config_class)

    # New method that is more robust to get checkpoints!

    if checkpoint is None and not processor_class.__name__.startswith("Auto"):
        # try to get the checkpoint from the config class for `processor_class`.
        # This helps cases like `XCLIPConfig` and `VideoMAEFeatureExtractor` to find a checkpoint from `VideoMAEConfig`.
        config_class_from_processor_class = get_config_class_from_processor_class(processor_class)
        checkpoint = get_checkpoint_from_config_class(config_class_from_processor_class)

    processor = None
    try:
        revision = CHECKPOINT_REVISIONS.get(config_class.__name__)
        sub_folder = CHECKPOINT_SUBFOLDERS.get(config_class.__name__, "")
        processor = processor_class.from_pretrained(checkpoint, revision=revision, subfolder=sub_folder)
    except Exception as e:
        logger.error(f"{e.__class__.__name__}: {e}")

    # Try to get a new processor class from checkpoint. This is helpful for a checkpoint without necessary file to load
    # processor while `processor_class` is an Auto class. For example, `sew` has `Wav2Vec2Processor` in
    # `PROCESSOR_MAPPING_NAMES`, its `tokenizer_class` is `AutoTokenizer`, and the checkpoint
    # `https://huggingface.co/asapp/sew-tiny-100k` has no tokenizer file, but we can get
    # `tokenizer_class: Wav2Vec2CTCTokenizer` from the config file. (The new processor class won't be able to load from
    # `checkpoint`, but it helps this recursive method to find a way to build a processor).
    if (
        processor is None
        and checkpoint is not None
        and issubclass(processor_class, (PreTrainedTokenizerBase, AutoTokenizer))
    ):
        try:
            revision = CHECKPOINT_REVISIONS.get(config_class.__name__)
            config = AutoConfig.from_pretrained(checkpoint, revision=revision)
        except Exception as e:
            logger.error(f"{e.__class__.__name__}: {e}")
            config = None
        if config is not None:
            # TODO: sam2 (Sam2Config) from `facebook/sam2.1-hiera-tiny` will fail if we don't add `getattr(config, "tokenizer_class", None) is not None`
            # (as we get `Sam2VideoConfig` instead of `Sam2Config`)
            if getattr(config, "tokenizer_class", None) is not None and not isinstance(config, config_class):
                raise ValueError(
                    f"`config` (which is of type {config.__class__.__name__}) should be an instance of `config_class`"
                    f" ({config_class.__name__})!"
                )
            if getattr(config, "tokenizer_class", None) is not None:
                tokenizer_class = config.tokenizer_class
                new_processor_class = None
                if tokenizer_class is not None:
                    # Some hub configs have the wrong values!!! (e.g. it is `CPMAntTokenizer` but should be `CpmAntTokenizer`)
                    new_processor_class = getattr(transformers_module, tokenizer_class, None)

                    if new_processor_class is not None and new_processor_class != processor_class:
                        processor = build_processor(config_class, new_processor_class)
                # If `tokenizer_class` is not specified in `config`, let's use `config` to get the process class via auto
                # mappings, but only allow the tokenizer mapping being used. This is to make `Wav2Vec2Conformer` build
                if processor is None:
                    new_processor_classes = get_processor_types_from_config_class(
                        config.__class__, allowed_mappings=["tokenizer"]
                    )
                    # Used to avoid infinite recursion between a pair of fast/slow tokenizer types
                    names = [
                        x.__name__.replace("Fast", "") for x in [processor_class, new_processor_class] if x is not None
                    ]
                    new_processor_classes = [
                        x
                        for x in new_processor_classes
                        if x is not None and x.__name__.replace("Fast", "") not in names
                    ]
                    # For recursive calls, let's avoid `Auto`!!!
                    new_processor_classes = [x for x in new_processor_classes if not x.__name__.startswith("Auto")]

                    if len(new_processor_classes) > 0:
                        new_processor_class = new_processor_classes[0]
                        # Let's use fast tokenizer if there is any
                        # TODO: this is likely be very misleading!!!
                        for x in new_processor_classes:
                            if x.__name__.endswith("Fast"):
                                new_processor_class = x
                                break
                        processor = build_processor(config_class, new_processor_class)

    if processor is None:
        # # Try to build each component (tokenizer & feature extractor) of a `ProcessorMixin`.
        # if issubclass(processor_class, ProcessorMixin):
        #     attrs = {}
        #     for attr_name in processor_class.get_attributes():
        #         attrs[attr_name] = []
        #         # This could be a tuple (for tokenizers). For example, `CLIPProcessor` has
        #         #   - feature_extractor_class = "CLIPFeatureExtractor"
        #         #   - tokenizer_class = ("CLIPTokenizer", "CLIPTokenizerFast")
        #         try:
        #             attr_class_names = getattr(processor_class, f"{attr_name}_class")
        #         except:
        #             # breakpoint()
        #         if not isinstance(attr_class_names, tuple):
        #             attr_class_names = (attr_class_names,)
        #
        #         for name in attr_class_names:
        #             attr_class = getattr(transformers_module, name)
        #             attr = build_processor(config_class, attr_class)
        #             if attr is not None:
        #                 attrs[attr_name].append(attr)
        #
        #     # try to build a `ProcessorMixin`, so we can return a single value
        #     if all(len(v) > 0 for v in attrs.values()):
        #         try:
        #             processor = processor_class(**{k: v[0] for k, v in attrs.items()})
        #         except Exception as e:
        #             logger.error(f"{e.__class__.__name__}: {e}")
        if not processor_class.__name__.startswith("Auto"):
            # `checkpoint` might lack some file(s) to load a processor. For example, `facebook/hubert-base-ls960`
            # has no tokenizer file to load `Wav2Vec2CTCTokenizer`. In this case, we try to build a processor
            # with the configuration class (for example, `Wav2Vec2Config`) corresponding to `processor_class`.
            config_class_from_processor_class = get_config_class_from_processor_class(processor_class)
            if config_class_from_processor_class != config_class:
                processor = build_processor(config_class_from_processor_class, processor_class)

    # Try to create an image processor or a feature extractor without any checkpoint
    if (
        processor is None
        and allow_no_checkpoint
        and (issubclass(processor_class, BaseImageProcessor) or issubclass(processor_class, FeatureExtractionMixin))
    ):
        try:
            processor = processor_class()
        except Exception as e:
            logger.error(f"{e.__class__.__name__}: {e}")

    # validation
    # TODO: We might get `TokenizersBackend` in a recursive call (using `AutoTokenizer` class) and might fail if we don't add the condition
    # `isinstance(processor, TokenizersBackend)`!! (e.g. Yoso!)
    if processor is not None:
        if not (
            isinstance(processor, processor_class)
            or isinstance(processor, TokenizersBackend)
            or processor_class.__name__.startswith("Auto")
        ):
            raise ValueError(
                f"`processor` (which is of type {processor.__class__.__name__}) should be an instance of"
                f" {processor_class.__name__} or an Auto class!"
            )

    return processor