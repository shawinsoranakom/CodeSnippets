def filter_completion[TCompletionConfig: CompletionConfig](
    completion: dict[str, TCompletionConfig],
    controller_only: bool = False,
    include_defaults: bool = False,
) -> dict[str, TCompletionConfig]:
    """Return the given completion dictionary, filtering out configs which do not support the controller if controller_only is specified."""
    if controller_only:
        # The cast is needed because mypy gets confused here and forgets that completion values are TCompletionConfig.
        completion = {name: t.cast(TCompletionConfig, config) for name, config in completion.items() if
                      isinstance(config, PosixCompletionConfig) and config.controller_supported}

    if not include_defaults:
        completion = {name: config for name, config in completion.items() if not config.is_default}

    return completion