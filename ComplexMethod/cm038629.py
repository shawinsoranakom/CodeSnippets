def get_logits_processors(
    processors: LogitsProcessors | None, pattern: str | None
) -> list[Any] | None:
    if processors and pattern:
        logits_processors = []
        for processor in processors:
            qualname = processor if isinstance(processor, str) else processor.qualname
            if not re.match(pattern, qualname):
                raise ValueError(
                    f"Logits processor '{qualname}' is not allowed by this "
                    "server. See --logits-processor-pattern engine argument "
                    "for more information."
                )
            try:
                logits_processor = resolve_obj_by_qualname(qualname)
            except Exception as e:
                raise ValueError(
                    f"Logits processor '{qualname}' could not be resolved: {e}"
                ) from e
            if isinstance(processor, LogitsProcessorConstructor):
                logits_processor = logits_processor(
                    *processor.args or [], **processor.kwargs or {}
                )
            logits_processors.append(logits_processor)
        return logits_processors
    elif processors:
        raise ValueError(
            "The `logits_processors` argument is not supported by this "
            "server. See --logits-processor-pattern engine argument "
            "for more information."
        )
    return None