def pipeline(
    task: str | None = None,
    model: str | PreTrainedModel | None = None,
    config: str | PreTrainedConfig | None = None,
    tokenizer: str | PreTrainedTokenizer | PreTrainedTokenizerFast | None = None,
    feature_extractor: str | PreTrainedFeatureExtractor | None = None,
    image_processor: str | BaseImageProcessor | None = None,
    processor: str | ProcessorMixin | None = None,
    revision: str | None = None,
    use_fast: bool = True,
    token: str | bool | None = None,
    device: int | str | torch.device | None = None,
    device_map: str | dict[str, int | str] | None = None,
    dtype: str | torch.dtype | None = "auto",
    trust_remote_code: bool | None = None,
    model_kwargs: dict[str, Any] | None = None,
    pipeline_class: Any | None = None,
    **kwargs: Any,
) -> Pipeline:
    """
    Utility factory method to build a [`Pipeline`].

    A pipeline consists of:

        - One or more components for pre-processing model inputs, such as a [tokenizer](tokenizer),
        [image_processor](image_processor), [feature_extractor](feature_extractor), or [processor](processors).
        - A [model](model) that generates predictions from the inputs.
        - Optional post-processing steps to refine the model's output, which can also be handled by processors.

    <Tip>
    While there are such optional arguments as `tokenizer`, `feature_extractor`, `image_processor`, and `processor`,
    they shouldn't be specified all at once. If these components are not provided, `pipeline` will try to load
    required ones automatically. In case you want to provide these components explicitly, please refer to a
    specific pipeline in order to get more details regarding what components are required.
    </Tip>

    Args:
        task (`str`):
            The task defining which pipeline will be returned. Currently accepted tasks are:

            - `"audio-classification"`: will return a [`AudioClassificationPipeline`].
            - `"automatic-speech-recognition"`: will return a [`AutomaticSpeechRecognitionPipeline`].
            - `"depth-estimation"`: will return a [`DepthEstimationPipeline`].
            - `"document-question-answering"`: will return a [`DocumentQuestionAnsweringPipeline`].
            - `"feature-extraction"`: will return a [`FeatureExtractionPipeline`].
            - `"fill-mask"`: will return a [`FillMaskPipeline`]:.
            - `"image-classification"`: will return a [`ImageClassificationPipeline`].
            - `"image-feature-extraction"`: will return an [`ImageFeatureExtractionPipeline`].
            - `"image-segmentation"`: will return a [`ImageSegmentationPipeline`].
            - `"image-text-to-text"`: will return a [`ImageTextToTextPipeline`].
            - `"keypoint-matching"`: will return a [`KeypointMatchingPipeline`].
            - `"mask-generation"`: will return a [`MaskGenerationPipeline`].
            - `"object-detection"`: will return a [`ObjectDetectionPipeline`].
            - `"table-question-answering"`: will return a [`TableQuestionAnsweringPipeline`].
            - `"text-classification"` (alias `"sentiment-analysis"` available): will return a
              [`TextClassificationPipeline`].
            - `"text-generation"`: will return a [`TextGenerationPipeline`]:.
            - `"text-to-audio"` (alias `"text-to-speech"` available): will return a [`TextToAudioPipeline`]:.
            - `"token-classification"` (alias `"ner"` available): will return a [`TokenClassificationPipeline`].
            - `"video-classification"`: will return a [`VideoClassificationPipeline`].
            - `"zero-shot-classification"`: will return a [`ZeroShotClassificationPipeline`].
            - `"zero-shot-image-classification"`: will return a [`ZeroShotImageClassificationPipeline`].
            - `"zero-shot-audio-classification"`: will return a [`ZeroShotAudioClassificationPipeline`].
            - `"zero-shot-object-detection"`: will return a [`ZeroShotObjectDetectionPipeline`].

        model (`str` or [`PreTrainedModel`], *optional*):
            The model that will be used by the pipeline to make predictions. This can be a model identifier or an
            actual instance of a pretrained model inheriting from [`PreTrainedModel`].

            If not provided, the default for the `task` will be loaded.
        config (`str` or [`PreTrainedConfig`], *optional*):
            The configuration that will be used by the pipeline to instantiate the model. This can be a model
            identifier or an actual pretrained model configuration inheriting from [`PreTrainedConfig`].

            If not provided, the default configuration file for the requested model will be used. That means that if
            `model` is given, its default configuration will be used. However, if `model` is not supplied, this
            `task`'s default model's config is used instead.
        tokenizer (`str` or [`PreTrainedTokenizer`], *optional*):
            The tokenizer that will be used by the pipeline to encode data for the model. This can be a model
            identifier or an actual pretrained tokenizer inheriting from [`PreTrainedTokenizer`].

            If not provided, the default tokenizer for the given `model` will be loaded (if it is a string). If `model`
            is not specified or not a string, then the default tokenizer for `config` is loaded (if it is a string).
            However, if `config` is also not given or not a string, then the default tokenizer for the given `task`
            will be loaded.
        feature_extractor (`str` or [`PreTrainedFeatureExtractor`], *optional*):
            The feature extractor that will be used by the pipeline to encode data for the model. This can be a model
            identifier or an actual pretrained feature extractor inheriting from [`PreTrainedFeatureExtractor`].

            Feature extractors are used for non-NLP models, such as Speech or Vision models as well as multi-modal
            models. Multi-modal models will also require a tokenizer to be passed.

            If not provided, the default feature extractor for the given `model` will be loaded (if it is a string). If
            `model` is not specified or not a string, then the default feature extractor for `config` is loaded (if it
            is a string). However, if `config` is also not given or not a string, then the default feature extractor
            for the given `task` will be loaded.
        image_processor (`str` or [`BaseImageProcessor`], *optional*):
            The image processor that will be used by the pipeline to preprocess images for the model. This can be a
            model identifier or an actual image processor inheriting from [`BaseImageProcessor`].

            Image processors are used for Vision models and multi-modal models that require image inputs. Multi-modal
            models will also require a tokenizer to be passed.

            If not provided, the default image processor for the given `model` will be loaded (if it is a string). If
            `model` is not specified or not a string, then the default image processor for `config` is loaded (if it is
            a string).
        processor (`str` or [`ProcessorMixin`], *optional*):
            The processor that will be used by the pipeline to preprocess data for the model. This can be a model
            identifier or an actual processor inheriting from [`ProcessorMixin`].

            Processors are used for multi-modal models that require multi-modal inputs, for example, a model that
            requires both text and image inputs.

            If not provided, the default processor for the given `model` will be loaded (if it is a string). If `model`
            is not specified or not a string, then the default processor for `config` is loaded (if it is a string).
        revision (`str`, *optional*, defaults to `"main"`):
            When passing a task name or a string model identifier: The specific model version to use. It can be a
            branch name, a tag name, or a commit id, since we use a git-based system for storing models and other
            artifacts on huggingface.co, so `revision` can be any identifier allowed by git.
        use_fast (`bool`, *optional*, defaults to `True`):
            Whether or not to use a Fast tokenizer if possible (a [`PreTrainedTokenizerFast`]).
        token (`str` or *bool*, *optional*):
            The token to use as HTTP bearer authorization for remote files. If `True`, will use the token generated
            when running `hf auth login`.
        device (`int` or `str` or `torch.device`):
            Defines the device (*e.g.*, `"cpu"`, `"cuda:1"`, `"mps"`, or a GPU ordinal rank like `1`) on which this
            pipeline will be allocated.
        device_map (`str` or `dict[str, Union[int, str, torch.device]`, *optional*):
            Sent directly as `model_kwargs` (just a simpler shortcut). When `accelerate` library is present, set
            `device_map="auto"` to compute the most optimized `device_map` automatically (see
            [here](https://huggingface.co/docs/accelerate/main/en/package_reference/big_modeling#accelerate.cpu_offload)
            for more information).

            <Tip warning={true}>

            Do not use `device_map` AND `device` at the same time as they will conflict

            </Tip>

        dtype (`str` or `torch.dtype`, *optional*):
            Sent directly as `model_kwargs` (just a simpler shortcut) to use the available precision for this model
            (`torch.float16`, `torch.bfloat16`, ... or `"auto"`).
        trust_remote_code (`bool`, *optional*, defaults to `False`):
            Whether or not to allow for custom code defined on the Hub in their own modeling, configuration,
            tokenization or even pipeline files. This option should only be set to `True` for repositories you trust
            and in which you have read the code, as it will execute code present on the Hub on your local machine.
        model_kwargs (`dict[str, Any]`, *optional*):
            Additional dictionary of keyword arguments passed along to the model's `from_pretrained(...,
            **model_kwargs)` function.
        kwargs (`dict[str, Any]`, *optional*):
            Additional keyword arguments passed along to the specific pipeline init (see the documentation for the
            corresponding pipeline class for possible values).

    Returns:
        [`Pipeline`]: A suitable pipeline for the task.

    Examples:

    ```python
    >>> from transformers import pipeline, AutoModelForTokenClassification, AutoTokenizer

    >>> # Sentiment analysis pipeline
    >>> analyzer = pipeline("sentiment-analysis")

    >>> # Named entity recognition pipeline, passing in a specific model and tokenizer
    >>> model = AutoModelForTokenClassification.from_pretrained("dbmdz/bert-large-cased-finetuned-conll03-english")
    >>> tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-cased")
    >>> recognizer = pipeline("ner", model=model, tokenizer=tokenizer)
    ```"""
    if model_kwargs is None:
        model_kwargs = {}

    code_revision = kwargs.pop("code_revision", None)
    commit_hash = kwargs.pop("_commit_hash", None)
    local_files_only = kwargs.get("local_files_only", False)

    hub_kwargs = {
        "revision": revision,
        "token": token,
        "trust_remote_code": trust_remote_code,
        "_commit_hash": commit_hash,
        "local_files_only": local_files_only,
    }

    if task is None and model is None:
        raise RuntimeError(
            "Impossible to instantiate a pipeline without either a task or a model "
            "being specified. "
            "Please provide a task class or a model"
        )

    if model is None and tokenizer is not None:
        raise RuntimeError(
            "Impossible to instantiate a pipeline with tokenizer specified but not the model as the provided tokenizer"
            " may not be compatible with the default model. Please provide a PreTrainedModel class or a"
            " path/identifier to a pretrained model when providing tokenizer."
        )
    if model is None and feature_extractor is not None:
        raise RuntimeError(
            "Impossible to instantiate a pipeline with feature_extractor specified but not the model as the provided"
            " feature_extractor may not be compatible with the default model. Please provide a PreTrainedModel class"
            " or a path/identifier to a pretrained model when providing feature_extractor."
        )
    if isinstance(model, Path):
        model = str(model)

    if commit_hash is None:
        pretrained_model_name_or_path = None
        if isinstance(config, str):
            pretrained_model_name_or_path = config
        elif config is None and isinstance(model, str):
            pretrained_model_name_or_path = model

        if not isinstance(config, PreTrainedConfig) and pretrained_model_name_or_path is not None:
            # We make a call to the config file first (which may be absent) to get the commit hash as soon as possible
            resolved_config_file = cached_file(
                pretrained_model_name_or_path,
                CONFIG_NAME,
                _raise_exceptions_for_gated_repo=False,
                _raise_exceptions_for_missing_entries=False,
                _raise_exceptions_for_connection_errors=False,
                cache_dir=model_kwargs.get("cache_dir"),
                **hub_kwargs,
            )
            hub_kwargs["_commit_hash"] = extract_commit_hash(resolved_config_file, commit_hash)
        else:
            hub_kwargs["_commit_hash"] = getattr(config, "_commit_hash", None)

    # Config is the primordial information item.
    # Instantiate config if needed
    adapter_path = None
    if isinstance(config, str):
        config = AutoConfig.from_pretrained(
            config, _from_pipeline=task, code_revision=code_revision, **hub_kwargs, **model_kwargs
        )
        hub_kwargs["_commit_hash"] = config._commit_hash
    elif config is None and isinstance(model, str):
        # Check for an adapter file in the model path if PEFT is available
        if is_peft_available():
            # `find_adapter_config_file` doesn't accept `trust_remote_code`
            _hub_kwargs = {k: v for k, v in hub_kwargs.items() if k != "trust_remote_code"}
            maybe_adapter_path = find_adapter_config_file(
                model,
                token=hub_kwargs["token"],
                revision=hub_kwargs["revision"],
                _commit_hash=hub_kwargs["_commit_hash"],
            )

            if maybe_adapter_path is not None:
                with open(maybe_adapter_path, "r", encoding="utf-8") as f:
                    adapter_config = json.load(f)
                    adapter_path = model
                    # Only override the model name/path if the current value doesn't point to a
                    # complete model with an embedded adapter so that local models with embedded
                    # adapters will load from the local base model rather than pull the base
                    # model named in the adapter's config from the hub.
                    if not os.path.exists(model) or not os.path.exists(os.path.join(model, CONFIG_NAME)):
                        model = adapter_config["base_model_name_or_path"]

        config = AutoConfig.from_pretrained(
            model, _from_pipeline=task, code_revision=code_revision, **hub_kwargs, **model_kwargs
        )
        hub_kwargs["_commit_hash"] = config._commit_hash

    custom_tasks = {}
    if config is not None and len(getattr(config, "custom_pipelines", {})) > 0:
        custom_tasks = config.custom_pipelines
        if task is None and trust_remote_code is not False:
            if len(custom_tasks) == 1:
                task = list(custom_tasks.keys())[0]
            else:
                raise RuntimeError(
                    "We can't infer the task automatically for this model as there are multiple tasks available. Pick "
                    f"one in {', '.join(custom_tasks.keys())}"
                )

    if task is None and model is not None:
        if not isinstance(model, str):
            raise RuntimeError(
                "Inferring the task automatically requires to check the hub with a model_id defined as a `str`. "
                f"{model} is not a valid model_id."
            )
        task = get_task(model, token)

    # Retrieve the task
    if task in custom_tasks:
        targeted_task, task_options = clean_custom_task(custom_tasks[task])
        if pipeline_class is None:
            if not trust_remote_code:
                raise ValueError(
                    "Loading this pipeline requires you to execute the code in the pipeline file in that"
                    " repo on your local machine. Make sure you have read the code there to avoid malicious use, then"
                    " set the option `trust_remote_code=True` to remove this error."
                )
            class_ref = targeted_task["impl"]
            pipeline_class = get_class_from_dynamic_module(
                class_ref,
                model,
                code_revision=code_revision,
                **hub_kwargs,
            )
    else:
        normalized_task, targeted_task, task_options = check_task(task)
        if pipeline_class is None:
            pipeline_class = targeted_task["impl"]

    # Use default model/config/tokenizer for the task if no model is provided
    if model is None:
        model, default_revision = get_default_model_and_revision(targeted_task, task_options)
        revision = revision if revision is not None else default_revision
        logger.warning(
            f"No model was supplied, defaulted to {model} and revision {revision}.\n"
            "Using a pipeline without specifying a model name and revision in production is not recommended."
        )
        hub_kwargs["revision"] = revision
        if config is None and isinstance(model, str):
            config = AutoConfig.from_pretrained(model, _from_pipeline=task, **hub_kwargs, **model_kwargs)
            hub_kwargs["_commit_hash"] = config._commit_hash

    if device_map is not None:
        if "device_map" in model_kwargs:
            raise ValueError(
                'You cannot use both `pipeline(... device_map=..., model_kwargs={"device_map":...})` as those'
                " arguments might conflict, use only one.)"
            )
        if device is not None:
            logger.warning(
                "Both `device` and `device_map` are specified. `device` will override `device_map`. You"
                " will most likely encounter unexpected behavior. Please remove `device` and keep `device_map`."
            )
        model_kwargs["device_map"] = device_map

    # BC for the `torch_dtype` argument
    if (torch_dtype := kwargs.get("torch_dtype")) is not None:
        logger.warning_once("`torch_dtype` is deprecated! Use `dtype` instead!")
        # If both are provided, keep `dtype`
        dtype = torch_dtype if dtype == "auto" else dtype
    if "torch_dtype" in model_kwargs or "dtype" in model_kwargs:
        if "torch_dtype" in model_kwargs:
            logger.warning_once("`torch_dtype` is deprecated! Use `dtype` instead!")
        # If the user did not explicitly provide `dtype` (i.e. the function default "auto" is still
        # present) but a value is supplied inside `model_kwargs`, we silently defer to the latter instead of
        # raising. This prevents false positives like providing `dtype` only via `model_kwargs` while the
        # top-level argument keeps its default value "auto".
        if dtype == "auto":
            dtype = None
        else:
            raise ValueError(
                'You cannot use both `pipeline(... dtype=..., model_kwargs={"dtype":...})` as those'
                " arguments might conflict, use only one.)"
            )
    if dtype is not None:
        if isinstance(dtype, str) and hasattr(torch, dtype):
            dtype = getattr(torch, dtype)
        model_kwargs["dtype"] = dtype

    model_name = model if isinstance(model, str) else None

    # Load the correct model if possible
    if isinstance(model, str):
        model_classes = targeted_task["pt"]
        model = load_model(
            adapter_path if adapter_path is not None else model,
            model_classes=model_classes,
            config=config,
            task=task,
            **hub_kwargs,
            **model_kwargs,
        )

    hub_kwargs["_commit_hash"] = model.config._commit_hash

    # Check which preprocessing classes the pipeline uses
    # None values indicate optional classes that the pipeline can run without, we don't raise errors if loading fails
    load_tokenizer = pipeline_class._load_tokenizer
    load_feature_extractor = pipeline_class._load_feature_extractor
    load_image_processor = pipeline_class._load_image_processor
    load_processor = pipeline_class._load_processor

    if load_tokenizer or load_tokenizer is None:
        try:
            # Try to infer tokenizer from model or config name (if provided as str)
            if tokenizer is None:
                if isinstance(model_name, str):
                    tokenizer = model_name
                elif isinstance(config, str):
                    tokenizer = config
                else:
                    # Impossible to guess what is the right tokenizer here
                    raise Exception(
                        "Impossible to guess which tokenizer to use. "
                        "Please provide a PreTrainedTokenizer class or a path/identifier to a pretrained tokenizer."
                    )

            # Instantiate tokenizer if needed
            if isinstance(tokenizer, (str, tuple)):
                if isinstance(tokenizer, tuple):
                    # For tuple we have (tokenizer name, {kwargs})
                    use_fast = tokenizer[1].pop("use_fast", use_fast)
                    tokenizer_identifier = tokenizer[0]
                    tokenizer_kwargs = tokenizer[1]
                else:
                    tokenizer_identifier = tokenizer
                    tokenizer_kwargs = model_kwargs.copy()
                    tokenizer_kwargs.pop("torch_dtype", None), tokenizer_kwargs.pop("dtype", None)

                tokenizer = AutoTokenizer.from_pretrained(
                    tokenizer_identifier, use_fast=use_fast, _from_pipeline=task, **hub_kwargs, **tokenizer_kwargs
                )
        except Exception as e:
            if load_tokenizer:
                raise e
            else:
                tokenizer = None

    if load_image_processor or load_image_processor is None:
        try:
            # Try to infer image processor from model or config name (if provided as str)
            if image_processor is None:
                if isinstance(model_name, str):
                    image_processor = model_name
                elif isinstance(config, str):
                    image_processor = config
                # Backward compatibility, as `feature_extractor` used to be the name
                # for `ImageProcessor`.
                elif feature_extractor is not None and isinstance(feature_extractor, BaseImageProcessor):
                    image_processor = feature_extractor
                else:
                    # Impossible to guess what is the right image_processor here
                    raise Exception(
                        "Impossible to guess which image processor to use. "
                        "Please provide a PreTrainedImageProcessor class or a path/identifier "
                        "to a pretrained image processor."
                    )

            # Instantiate image_processor if needed
            if isinstance(image_processor, (str, tuple)):
                image_processor = AutoImageProcessor.from_pretrained(
                    image_processor, _from_pipeline=task, **hub_kwargs, **model_kwargs
                )
        except Exception as e:
            if load_image_processor:
                raise e
            else:
                image_processor = None

    if load_feature_extractor or load_feature_extractor is None:
        try:
            # Try to infer feature extractor from model or config name (if provided as str)
            if feature_extractor is None:
                if isinstance(model_name, str):
                    feature_extractor = model_name
                elif isinstance(config, str):
                    feature_extractor = config
                else:
                    # Impossible to guess what is the right feature_extractor here
                    raise Exception(
                        "Impossible to guess which feature extractor to use. "
                        "Please provide a PreTrainedFeatureExtractor class or a path/identifier "
                        "to a pretrained feature extractor."
                    )

            # Instantiate feature_extractor if needed
            if isinstance(feature_extractor, (str, tuple)):
                feature_extractor = AutoFeatureExtractor.from_pretrained(
                    feature_extractor, _from_pipeline=task, **hub_kwargs, **model_kwargs
                )
                config_dict, _ = FeatureExtractionMixin.get_feature_extractor_dict(
                    pretrained_model_name_or_path or model_name,
                    **hub_kwargs,
                )
                processor_class = config_dict.get("processor_class", None)

                if processor_class is not None and processor_class.endswith("WithLM") and isinstance(model_name, str):
                    try:
                        import kenlm  # to trigger `ImportError` if not installed
                        from pyctcdecode import BeamSearchDecoderCTC

                        if os.path.isdir(model_name) or os.path.isfile(model_name):
                            decoder = BeamSearchDecoderCTC.load_from_dir(model_name)
                        else:
                            language_model_glob = os.path.join(
                                BeamSearchDecoderCTC._LANGUAGE_MODEL_SERIALIZED_DIRECTORY, "*"
                            )
                            alphabet_filename = BeamSearchDecoderCTC._ALPHABET_SERIALIZED_FILENAME
                            allow_patterns = [language_model_glob, alphabet_filename]
                            decoder = BeamSearchDecoderCTC.load_from_hf_hub(model_name, allow_patterns=allow_patterns)

                        kwargs["decoder"] = decoder
                    except ImportError as e:
                        logger.warning(
                            f"Could not load the `decoder` for {model_name}. Defaulting to raw CTC. Error: {e}"
                        )
                        if not is_kenlm_available():
                            logger.warning("Try to install `kenlm`: `pip install kenlm")

                        if not is_pyctcdecode_available():
                            logger.warning("Try to install `pyctcdecode`: `pip install pyctcdecode")
        except Exception as e:
            if load_feature_extractor:
                raise e
            else:
                feature_extractor = None

    if load_processor or load_processor is None:
        try:
            # Try to infer processor from model or config name (if provided as str)
            if processor is None:
                if isinstance(model_name, str):
                    processor = model_name
                elif isinstance(config, str):
                    processor = config
                else:
                    # Impossible to guess what is the right processor here
                    raise Exception(
                        "Impossible to guess which processor to use. "
                        "Please provide a processor instance or a path/identifier "
                        "to a processor."
                    )

            # Instantiate processor if needed
            if isinstance(processor, (str, tuple)):
                processor = AutoProcessor.from_pretrained(processor, _from_pipeline=task, **hub_kwargs, **model_kwargs)
                if not isinstance(processor, ProcessorMixin):
                    raise TypeError(
                        "Processor was loaded, but it is not an instance of `ProcessorMixin`. "
                        f"Got type `{type(processor)}` instead. Please check that you specified "
                        "correct pipeline task for the model and model has processor implemented and saved."
                    )
        except Exception as e:
            if load_processor:
                raise e
            else:
                processor = None

    if tokenizer is not None:
        kwargs["tokenizer"] = tokenizer

    if feature_extractor is not None:
        kwargs["feature_extractor"] = feature_extractor

    if dtype is not None:
        kwargs["dtype"] = dtype

    if image_processor is not None:
        kwargs["image_processor"] = image_processor

    if device is not None:
        kwargs["device"] = device

    if processor is not None:
        kwargs["processor"] = processor

    return pipeline_class(model=model, task=task, **kwargs)