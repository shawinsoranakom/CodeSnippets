def from_pretrained(cls, pretrained_model_name_or_path, *inputs, **kwargs):
        r"""
        Instantiate one of the image processor classes of the library from a pretrained model vocabulary.

        The image processor class to instantiate is selected based on the `model_type` property of the config object
        (either passed as an argument or loaded from `pretrained_model_name_or_path` if possible), or when it's
        missing, by falling back to using pattern matching on `pretrained_model_name_or_path`:

        List options

        Params:
            pretrained_model_name_or_path (`str` or `os.PathLike`):
                This can be either:

                - a string, the *model id* of a pretrained image_processor hosted inside a model repo on
                  huggingface.co.
                - a path to a *directory* containing a image processor file saved using the
                  [`~image_processing_utils.ImageProcessingMixin.save_pretrained`] method, e.g.,
                  `./my_model_directory/`.
                - a path to a saved image processor JSON *file*, e.g.,
                  `./my_model_directory/preprocessor_config.json`.
            cache_dir (`str` or `os.PathLike`, *optional*):
                Path to a directory in which a downloaded pretrained model image processor should be cached if the
                standard cache should not be used.
            force_download (`bool`, *optional*, defaults to `False`):
                Whether or not to force to (re-)download the image processor files and override the cached versions if
                they exist.
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
            use_fast (`bool`, *optional*, defaults to `False`):
                **Deprecated**: Use `backend="torchvision"` instead. This parameter is kept for backward compatibility.
                Use a fast torchvision-based image processor if it is supported for a given model.
                If a fast image processor is not available for a given model, a normal numpy-based image processor
                is returned instead.
            backend (`str`, *optional*, defaults to `None`):
                The backend to use for image processing. Can be:
                - `None`: Automatically select the best available backend (torchvision if available, otherwise pil)
                - `"torchvision"`: Use Torchvision backend (GPU-accelerated, faster)
                - `"pil"`: Use PIL backend (portable, CPU-only)
                - Any custom backend name registered via `register()` method
            return_unused_kwargs (`bool`, *optional*, defaults to `False`):
                If `False`, then this function returns just the final image processor object. If `True`, then this
                functions returns a `Tuple(image_processor, unused_kwargs)` where *unused_kwargs* is a dictionary
                consisting of the key/value pairs whose keys are not image processor attributes: i.e., the part of
                `kwargs` which has not been used to update `image_processor` and is otherwise ignored.
            trust_remote_code (`bool`, *optional*, defaults to `False`):
                Whether or not to allow for custom models defined on the Hub in their own modeling files. This option
                should only be set to `True` for repositories you trust and in which you have read the code, as it will
                execute code present on the Hub on your local machine.
            image_processor_filename (`str`, *optional*, defaults to `"config.json"`):
                The name of the file in the model directory to use for the image processor config.
            kwargs (`dict[str, Any]`, *optional*):
                The values in kwargs of any keys which are image processor attributes will be used to override the
                loaded values. Behavior concerning key/value pairs whose keys are *not* image processor attributes is
                controlled by the `return_unused_kwargs` keyword parameter.

        <Tip>

        Passing `token=True` is required when you want to use a private model.

        </Tip>

        Examples:

        ```python
        >>> from transformers import AutoImageProcessor

        >>> # Download image processor from huggingface.co and cache.
        >>> image_processor = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")

        >>> # If image processor files are in a directory (e.g. image processor was saved using *save_pretrained('./test/saved_model/')*)
        >>> # image_processor = AutoImageProcessor.from_pretrained("./test/saved_model/")
        ```"""
        config = kwargs.pop("config", None)
        use_fast = kwargs.pop("use_fast", None)
        backend_kwarg = kwargs.pop("backend", None)
        trust_remote_code = kwargs.pop("trust_remote_code", None)
        kwargs["_from_auto"] = True

        # Resolve the image processor config filename
        if "image_processor_filename" in kwargs:
            image_processor_filename = kwargs.pop("image_processor_filename")
        elif is_timm_local_checkpoint(pretrained_model_name_or_path):
            image_processor_filename = CONFIG_NAME
        else:
            image_processor_filename = IMAGE_PROCESSOR_NAME

        # Load the image processor config

        try:
            config_dict, _ = ImageProcessingMixin.get_image_processor_dict(
                pretrained_model_name_or_path, image_processor_filename=image_processor_filename, **kwargs
            )
        except Exception as initial_exception:
            # Fallback for Hub TimmWrapper checkpoints (image processing in config.json, not preprocessor_config.json)
            try:
                config_dict, _ = ImageProcessingMixin.get_image_processor_dict(
                    pretrained_model_name_or_path, image_processor_filename=CONFIG_NAME, **kwargs
                )
            except Exception:
                raise initial_exception

            if not is_timm_config_dict(config_dict):
                raise initial_exception

        image_processor_type = config_dict.get("image_processor_type", None)
        image_processor_auto_map = None
        if "AutoImageProcessor" in config_dict.get("auto_map", {}):
            image_processor_auto_map = config_dict["auto_map"]["AutoImageProcessor"]

        # Backward compat: infer from feature extractor config
        if image_processor_type is None and image_processor_auto_map is None:
            feature_extractor_class = config_dict.pop("feature_extractor_type", None)
            if feature_extractor_class is not None:
                image_processor_type = feature_extractor_class.replace("FeatureExtractor", "ImageProcessor")
            if "AutoFeatureExtractor" in config_dict.get("auto_map", {}):
                feature_extractor_auto_map = config_dict["auto_map"]["AutoFeatureExtractor"]
                image_processor_auto_map = feature_extractor_auto_map.replace("FeatureExtractor", "ImageProcessor")

        # If not in image processor config, try the model config
        if image_processor_type is None and image_processor_auto_map is None:
            if not isinstance(config, PreTrainedConfig):
                config = AutoConfig.from_pretrained(
                    pretrained_model_name_or_path,
                    trust_remote_code=trust_remote_code,
                    **kwargs,
                )
            image_processor_type = getattr(config, "image_processor_type", None)
            if hasattr(config, "auto_map") and "AutoImageProcessor" in config.auto_map:
                image_processor_auto_map = config.auto_map["AutoImageProcessor"]

        # Derive base_class_name from image_processor_type
        is_legacy_fast = False
        base_class_name = None
        if image_processor_type is not None:
            is_legacy_fast = image_processor_type.endswith("Fast")
            base_class_name = image_processor_type[:-4] if is_legacy_fast else image_processor_type

        backend = _resolve_backend(backend_kwarg, use_fast, base_class_name)

        image_processor_class = None
        if base_class_name is not None:
            image_processor_class = _load_backend_class(base_class_name, backend, is_legacy_fast)

        # Handle remote code
        has_remote_code = image_processor_auto_map is not None
        has_local_code = image_processor_class is not None or type(config) in IMAGE_PROCESSOR_MAPPING
        explicit_local_code = has_local_code and not (
            image_processor_class or _load_class_with_fallback(IMAGE_PROCESSOR_MAPPING[type(config)], backend)
        ).__module__.startswith("transformers.")
        if has_remote_code:
            class_ref = _resolve_auto_map_class_ref(image_processor_auto_map, backend)
            upstream_repo = class_ref.split("--")[0] if "--" in class_ref else None
            trust_remote_code = resolve_trust_remote_code(
                trust_remote_code, pretrained_model_name_or_path, has_local_code, has_remote_code, upstream_repo
            )

        if has_remote_code and trust_remote_code and not explicit_local_code:
            image_processor_class = get_class_from_dynamic_module(class_ref, pretrained_model_name_or_path, **kwargs)
            _ = kwargs.pop("code_revision", None)
            image_processor_class.register_for_auto_class()
            return image_processor_class.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)
        elif image_processor_class is not None:
            return image_processor_class.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)
        # Last try: we use the IMAGE_PROCESSOR_MAPPING.
        elif type(config) in IMAGE_PROCESSOR_MAPPING:
            image_processor_mapping = IMAGE_PROCESSOR_MAPPING[type(config)]
            image_processor_class = _load_class_with_fallback(image_processor_mapping, backend)

            if image_processor_class is not None:
                return image_processor_class.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)

            available = [k for k, v in image_processor_mapping.items() if v is not None]
            raise ValueError(f"Could not find image processor class. Available backends: {', '.join(available)}")
        raise ValueError(
            f"Unrecognized image processor in {pretrained_model_name_or_path}. Should have a "
            f"`image_processor_type` key in its {IMAGE_PROCESSOR_NAME} of {CONFIG_NAME}, or one of the following "
            f"`model_type` keys in its {CONFIG_NAME}: {', '.join(c for c in IMAGE_PROCESSOR_MAPPING_NAMES)}"
        )