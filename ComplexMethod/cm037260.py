def _load_logitsprocs_by_fqcns(
    logits_processors: Sequence[str | type[LogitsProcessor]] | None,
) -> list[type[LogitsProcessor]]:
    """Load logit processor types, identifying them by fully-qualified class
    names (FQCNs).

    Effectively, a mixed list of logitproc types and FQCN strings is converted
    into a list of entirely logitproc types, by loading from the FQCNs.

    FQCN syntax is <module>:<type> i.e. x.y.z:CustomLogitProc

    Already-loaded logitproc types must be subclasses of LogitsProcessor

    Args:
      logits_processors: Potentially mixed list of logitsprocs types and FQCN
                         strings for logitproc types

    Returns:
      List of logitproc types

    """
    if not logits_processors:
        return []

    logger.debug(
        "%s additional custom logits processors specified, checking whether "
        "they need to be loaded.",
        len(logits_processors),
    )

    classes: list[type[LogitsProcessor]] = []
    for ldx, logitproc in enumerate(logits_processors):
        if isinstance(logitproc, type):
            logger.debug(" - Already-loaded logit processor: %s", logitproc.__name__)
            if not issubclass(logitproc, LogitsProcessor):
                raise ValueError(
                    f"{logitproc.__name__} is not a subclass of LogitsProcessor"
                )
            classes.append(logitproc)
            continue

        logger.debug("- Loading logits processor %s", logitproc)
        module_path, qualname = logitproc.split(":")

        try:
            # Load module
            with guard_cuda_initialization():
                module = importlib.import_module(module_path)
        except Exception as e:
            logger.error(
                "Failed to load %sth LogitsProcessor plugin %s: %s",
                ldx,
                logitproc,
                e,
            )
            raise RuntimeError(
                f"Failed to load {ldx}th LogitsProcessor plugin {logitproc}"
            ) from e

        # Walk down dotted name to get logitproc class
        obj = module
        for attr in qualname.split("."):
            obj = getattr(obj, attr)
        if not isinstance(obj, type):
            raise ValueError("Loaded logit processor must be a type.")
        if not issubclass(obj, LogitsProcessor):
            raise ValueError(f"{obj.__name__} must be a subclass of LogitsProcessor")
        classes.append(obj)

    return classes