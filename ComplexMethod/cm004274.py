def from_pretrained(cls, pretrained_model_name_or_path, **kwargs):
        r"""
        Instantiate one of the feature extractor classes of the library from a pretrained model vocabulary.

        The feature extractor class to instantiate is selected based on the `model_type` property of the config object
        (either passed as an argument or loaded from `pretrained_model_name_or_path` if possible), or when it's
        missing, by falling back to using pattern matching on `pretrained_model_name_or_path`:

        List options

        Params:
            pretrained_model_name_or_path (`str` or `os.PathLike`):
                This can be either:

                - a string, the *model id* of a pretrained feature_extractor hosted inside a model repo on
                  huggingface.co.
                - a path to a *directory* containing a feature extractor file saved using the
                  [`~feature_extraction_utils.FeatureExtractionMixin.save_pretrained`] method, e.g.,
                  `./my_model_directory/`.
                - a path to a saved feature extractor JSON *file*, e.g.,
                  `./my_model_directory/preprocessor_config.json`.
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
        >>> from transformers import AutoFeatureExtractor

        >>> # Download feature extractor from huggingface.co and cache.
        >>> feature_extractor = AutoFeatureExtractor.from_pretrained("facebook/wav2vec2-base-960h")

        >>> # If feature extractor files are in a directory (e.g. feature extractor was saved using *save_pretrained('./test/saved_model/')*)
        >>> # feature_extractor = AutoFeatureExtractor.from_pretrained("./test/saved_model/")
        ```"""
        config = kwargs.pop("config", None)
        trust_remote_code = kwargs.pop("trust_remote_code", None)
        kwargs["_from_auto"] = True

        config_dict, _ = FeatureExtractionMixin.get_feature_extractor_dict(pretrained_model_name_or_path, **kwargs)
        feature_extractor_class = config_dict.get("feature_extractor_type", None)
        feature_extractor_auto_map = None
        if "AutoFeatureExtractor" in config_dict.get("auto_map", {}):
            feature_extractor_auto_map = config_dict["auto_map"]["AutoFeatureExtractor"]

        # If we don't find the feature extractor class in the feature extractor config, let's try the model config.
        if feature_extractor_class is None and feature_extractor_auto_map is None:
            if not isinstance(config, PreTrainedConfig):
                config = AutoConfig.from_pretrained(
                    pretrained_model_name_or_path, trust_remote_code=trust_remote_code, **kwargs
                )
            # It could be in `config.feature_extractor_type``
            feature_extractor_class = getattr(config, "feature_extractor_type", None)
            if hasattr(config, "auto_map") and "AutoFeatureExtractor" in config.auto_map:
                feature_extractor_auto_map = config.auto_map["AutoFeatureExtractor"]

        if feature_extractor_class is not None:
            feature_extractor_class = feature_extractor_class_from_name(feature_extractor_class)

        has_remote_code = feature_extractor_auto_map is not None
        has_local_code = feature_extractor_class is not None or type(config) in FEATURE_EXTRACTOR_MAPPING
        explicit_local_code = has_local_code and not (
            feature_extractor_class or FEATURE_EXTRACTOR_MAPPING[type(config)]
        ).__module__.startswith("transformers.")
        if has_remote_code:
            if "--" in feature_extractor_auto_map:
                upstream_repo = feature_extractor_auto_map.split("--")[0]
            else:
                upstream_repo = None
            trust_remote_code = resolve_trust_remote_code(
                trust_remote_code, pretrained_model_name_or_path, has_local_code, has_remote_code, upstream_repo
            )

        if has_remote_code and trust_remote_code and not explicit_local_code:
            feature_extractor_class = get_class_from_dynamic_module(
                feature_extractor_auto_map, pretrained_model_name_or_path, **kwargs
            )
            _ = kwargs.pop("code_revision", None)
            feature_extractor_class.register_for_auto_class()
            return feature_extractor_class.from_pretrained(pretrained_model_name_or_path, **kwargs)
        elif feature_extractor_class is not None:
            return feature_extractor_class.from_pretrained(pretrained_model_name_or_path, **kwargs)
        # Last try: we use the FEATURE_EXTRACTOR_MAPPING.
        elif type(config) in FEATURE_EXTRACTOR_MAPPING:
            feature_extractor_class = FEATURE_EXTRACTOR_MAPPING[type(config)]
            return feature_extractor_class.from_pretrained(pretrained_model_name_or_path, **kwargs)

        raise ValueError(
            f"Unrecognized feature extractor in {pretrained_model_name_or_path}. Should have a "
            f"`feature_extractor_type` key in its {FEATURE_EXTRACTOR_NAME} of {CONFIG_NAME}, or one of the following "
            f"`model_type` keys in its {CONFIG_NAME}: {', '.join(c for c in FEATURE_EXTRACTOR_MAPPING_NAMES)}"
        )