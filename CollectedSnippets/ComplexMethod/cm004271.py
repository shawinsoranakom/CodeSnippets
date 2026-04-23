def from_pretrained(cls, pretrained_model_name_or_path, **kwargs):
        r"""
        Instantiate one of the processor classes of the library from a pretrained model vocabulary.

        The processor class to instantiate is selected based on the `model_type` property of the config object (either
        passed as an argument or loaded from `pretrained_model_name_or_path` if possible):

        List options

        Params:
            pretrained_model_name_or_path (`str` or `os.PathLike`):
                This can be either:

                - a string, the *model id* of a pretrained feature_extractor hosted inside a model repo on
                  huggingface.co.
                - a path to a *directory* containing a processor files saved using the `save_pretrained()` method,
                  e.g., `./my_model_directory/`.
            cache_dir (`str` or `os.PathLike`, *optional*):
                Path to a directory in which a downloaded pretrained model feature extractor should be cached if the
                standard cache should not be used.
            force_download (`bool`, *optional*, defaults to `False`):
                Whether or not to force to (re-)download the feature extractor files and override the cached versions
                if they exist.
            proxies (`dict[str, str]`, *optional*):
                A dictionary of proxy servers to use by protocol or endpoint, e.g., `{'http': 'foo.bar:3128',
                'http://hostname': 'foo.bar:4012'}.` The proxies are used on each request.
            token (`str` or *bool*, *optional*):
                The token to use as HTTP bearer authorization for remote files. If `True`, will use the token generated
                when running `hf auth login` (stored in `~/.huggingface`).
            revision (`str`, *optional*, defaults to `"main"`):
                The specific model version to use. It can be a branch name, a tag name, or a commit id, since we use a
                git-based system for storing models and other artifacts on huggingface.co, so `revision` can be any
                identifier allowed by git.
            return_unused_kwargs (`bool`, *optional*, defaults to `False`):
                If `False`, then this function returns just the final feature extractor object. If `True`, then this
                functions returns a `Tuple(feature_extractor, unused_kwargs)` where *unused_kwargs* is a dictionary
                consisting of the key/value pairs whose keys are not feature extractor attributes: i.e., the part of
                `kwargs` which has not been used to update `feature_extractor` and is otherwise ignored.
            trust_remote_code (`bool`, *optional*, defaults to `False`):
                Whether or not to allow for custom models defined on the Hub in their own modeling files. This option
                should only be set to `True` for repositories you trust and in which you have read the code, as it will
                execute code present on the Hub on your local machine.
            kwargs (`dict[str, Any]`, *optional*):
                The values in kwargs of any keys which are feature extractor attributes will be used to override the
                loaded values. Behavior concerning key/value pairs whose keys are *not* feature extractor attributes is
                controlled by the `return_unused_kwargs` keyword parameter.

        <Tip>

        Passing `token=True` is required when you want to use a private model.

        </Tip>

        Examples:

        ```python
        >>> from transformers import AutoProcessor

        >>> # Download processor from huggingface.co and cache.
        >>> processor = AutoProcessor.from_pretrained("facebook/wav2vec2-base-960h")

        >>> # If processor files are in a directory (e.g. processor was saved using *save_pretrained('./test/saved_model/')*)
        >>> # processor = AutoProcessor.from_pretrained("./test/saved_model/")
        ```"""
        config = kwargs.pop("config", None)
        trust_remote_code = kwargs.pop("trust_remote_code", None)
        kwargs["_from_auto"] = True

        processor_class = None
        processor_auto_map = None

        # First, let's see if we have a processor or preprocessor config.
        # Filter the kwargs for `cached_file`.
        _hub_valid_kwargs = (
            "cache_dir",
            "force_download",
            "proxies",
            "token",
            "revision",
            "local_files_only",
            "subfolder",
            "repo_type",
            "user_agent",
        )
        cached_file_kwargs = {key: kwargs[key] for key in _hub_valid_kwargs if key in kwargs}
        # We don't want to raise
        cached_file_kwargs.update(
            {
                "_raise_exceptions_for_gated_repo": False,
                "_raise_exceptions_for_missing_entries": False,
                "_raise_exceptions_for_connection_errors": False,
            }
        )

        # Let's start by checking whether the processor class is saved in a processor config
        processor_config_file = cached_file(pretrained_model_name_or_path, PROCESSOR_NAME, **cached_file_kwargs)
        if processor_config_file is not None:
            config_dict, _ = ProcessorMixin.get_processor_dict(pretrained_model_name_or_path, **kwargs)
            processor_class = config_dict.get("processor_class")
            if "AutoProcessor" in config_dict.get("auto_map", {}):
                processor_auto_map = config_dict["auto_map"]["AutoProcessor"]

        if processor_class is None:
            # If not found, let's check whether the processor class is saved in an image processor config
            preprocessor_config_file = cached_file(
                pretrained_model_name_or_path, FEATURE_EXTRACTOR_NAME, **cached_file_kwargs
            )
            if preprocessor_config_file is not None:
                config_dict, _ = ImageProcessingMixin.get_image_processor_dict(pretrained_model_name_or_path, **kwargs)
                processor_class = config_dict.get("processor_class", None)
                if "AutoProcessor" in config_dict.get("auto_map", {}):
                    processor_auto_map = config_dict["auto_map"]["AutoProcessor"]

            # Saved as video processor
            if preprocessor_config_file is None:
                preprocessor_config_file = cached_file(
                    pretrained_model_name_or_path, VIDEO_PROCESSOR_NAME, **cached_file_kwargs
                )
                if preprocessor_config_file is not None:
                    config_dict, _ = BaseVideoProcessor.get_video_processor_dict(
                        pretrained_model_name_or_path, **kwargs
                    )
                    processor_class = config_dict.get("processor_class", None)
                    if "AutoProcessor" in config_dict.get("auto_map", {}):
                        processor_auto_map = config_dict["auto_map"]["AutoProcessor"]
            # Saved as feature extractor
            if preprocessor_config_file is None:
                preprocessor_config_file = cached_file(
                    pretrained_model_name_or_path, FEATURE_EXTRACTOR_NAME, **cached_file_kwargs
                )
                if preprocessor_config_file is not None and processor_class is None:
                    config_dict, _ = FeatureExtractionMixin.get_feature_extractor_dict(
                        pretrained_model_name_or_path, **kwargs
                    )
                    processor_class = config_dict.get("processor_class", None)
                    if "AutoProcessor" in config_dict.get("auto_map", {}):
                        processor_auto_map = config_dict["auto_map"]["AutoProcessor"]

        if processor_class is None:
            # Next, let's check whether the processor class is saved in a tokenizer
            tokenizer_config_file = cached_file(
                pretrained_model_name_or_path, TOKENIZER_CONFIG_FILE, **cached_file_kwargs
            )
            if tokenizer_config_file is not None:
                with open(tokenizer_config_file, encoding="utf-8") as reader:
                    config_dict = json.load(reader)

                processor_class = config_dict.get("processor_class", None)
                if "AutoProcessor" in config_dict.get("auto_map", {}):
                    processor_auto_map = config_dict["auto_map"]["AutoProcessor"]

        if processor_class is None:
            # Last resort: try loading the model config to get processor_class.
            # This handles cases where processor info is only in config.json (not in any
            # preprocessor/tokenizer config files). AutoConfig.from_pretrained may raise
            # ValueError if the model_type is unrecognized or the config is invalid -
            # we catch and ignore this to allow fallback to AutoTokenizer/AutoImageProcessor.
            try:
                if not isinstance(config, PreTrainedConfig):
                    config = AutoConfig.from_pretrained(
                        pretrained_model_name_or_path, trust_remote_code=trust_remote_code, **kwargs
                    )

                processor_class = getattr(config, "processor_class", None)
                if hasattr(config, "auto_map") and "AutoProcessor" in config.auto_map:
                    processor_auto_map = config.auto_map["AutoProcessor"]
            except ValueError:
                # Config loading failed (unrecognized model_type, invalid config, etc.)
                # Continue to fallback logic below (AutoTokenizer, AutoImageProcessor, etc.)
                pass

        if processor_class is not None:
            processor_class = processor_class_from_name(processor_class)

        has_remote_code = processor_auto_map is not None
        has_local_code = processor_class is not None or type(config) in PROCESSOR_MAPPING
        explicit_local_code = has_local_code and not (
            processor_class or PROCESSOR_MAPPING[type(config)]
        ).__module__.startswith("transformers.")
        if has_remote_code:
            if "--" in processor_auto_map:
                upstream_repo = processor_auto_map.split("--")[0]
            else:
                upstream_repo = None
            trust_remote_code = resolve_trust_remote_code(
                trust_remote_code, pretrained_model_name_or_path, has_local_code, has_remote_code, upstream_repo
            )

        if has_remote_code and trust_remote_code and not explicit_local_code:
            processor_class = get_class_from_dynamic_module(
                processor_auto_map, pretrained_model_name_or_path, **kwargs
            )
            _ = kwargs.pop("code_revision", None)
            processor_class.register_for_auto_class()
            return processor_class.from_pretrained(
                pretrained_model_name_or_path, trust_remote_code=trust_remote_code, **kwargs
            )
        elif processor_class is not None:
            return processor_class.from_pretrained(
                pretrained_model_name_or_path, trust_remote_code=trust_remote_code, **kwargs
            )
        # Last try: we use the PROCESSOR_MAPPING.
        elif type(config) in PROCESSOR_MAPPING:
            return PROCESSOR_MAPPING[type(config)].from_pretrained(pretrained_model_name_or_path, **kwargs)

        # At this stage, there doesn't seem to be a `Processor` class available for this model.
        # Let's try the commonly available classes
        for klass in (AutoTokenizer, AutoImageProcessor, AutoVideoProcessor, AutoFeatureExtractor):
            try:
                return klass.from_pretrained(
                    pretrained_model_name_or_path, trust_remote_code=trust_remote_code, **kwargs
                )
            except Exception:
                continue

        raise ValueError(
            f"Unrecognized processing class in {pretrained_model_name_or_path}. Can't instantiate a processor, a "
            "tokenizer, an image processor, a video processor or a feature extractor for this model. "
            "Make sure the repository contains the files of at least one of those processing classes."
        )