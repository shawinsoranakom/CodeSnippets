def get_processor(
    processor_name: str,
    *args: Any,
    revision: str | None = None,
    trust_remote_code: bool = False,
    processor_cls: type[_P] | tuple[type[_P], ...] = ProcessorMixin,
    **kwargs: Any,
) -> _P:
    """Load a processor for the given model name via HuggingFace."""
    if revision is None:
        revision = "main"
    try:
        processor_name = convert_model_repo_to_path(processor_name)
        registered_cls_name = get_processor_cls_name_from_config(
            processor_name, revision=revision
        )
        registered_processor_cls = (
            getattr(processors, registered_cls_name, None)
            if registered_cls_name
            else None
        )
        registered_processor_cls = cast(type[_P] | None, registered_processor_cls)
        # Use registered processor class when it's available
        # and explicit processor_cls is not set.
        if isinstance(processor_cls, tuple) or processor_cls == ProcessorMixin:
            _processor_cls = registered_processor_cls or AutoProcessor
            processor = _processor_cls.from_pretrained(
                processor_name,
                *args,
                revision=revision,
                trust_remote_code=trust_remote_code,
                **kwargs,
            )
        elif issubclass(processor_cls, ProcessorMixin):
            processor = processor_cls.from_pretrained(
                processor_name,
                *args,
                revision=revision,
                trust_remote_code=trust_remote_code,
                **kwargs,
            )
        else:
            # Processors that are standalone classes unrelated to HF
            processor = processor_cls(*args, **kwargs)
    except ValueError as e:
        # If the error pertains to the processor class not existing or not
        # currently being imported, suggest using the --trust-remote-code flag.
        # Unlike AutoTokenizer, AutoProcessor does not separate such errors
        if not trust_remote_code:
            err_msg = (
                "Failed to load the processor. If the processor is "
                "a custom processor not yet available in the HuggingFace "
                "transformers library, consider setting "
                "`trust_remote_code=True` in LLM or using the "
                "`--trust-remote-code` flag in the CLI."
            )
            raise RuntimeError(err_msg) from e
        else:
            raise e

    if not isinstance(processor, processor_cls):
        raise TypeError(
            "Invalid type of HuggingFace processor. "
            f"Expected type: {processor_cls}, but "
            f"found type: {type(processor)}"
        )

    return processor