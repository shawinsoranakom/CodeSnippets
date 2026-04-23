def check_attribute_being_used(config_class, attributes, default_value, source_strings):
    """Check if any name in `attributes` is used in one of the strings in `source_strings`

    Args:
        config_class (`type`):
            The configuration class for which the arguments in its `__init__` will be checked.
        attributes (`List[str]`):
            The name of an argument (or attribute) and its variant names if any.
        default_value (`Any`):
            A default value for the attribute in `attributes` assigned in the `__init__` of `config_class`.
        source_strings (`List[str]`):
            The python source code strings in the same modeling directory where `config_class` is defined. The file
            containing the definition of `config_class` should be excluded.
    """
    # If we can find the attribute used, then it's all good
    for attribute in attributes:
        for modeling_source in source_strings:
            # check if we can find `config.xxx`, `getattr(config, "xxx", ...)` or `getattr(self.config, "xxx", ...)`
            if (
                f"config.{attribute}" in modeling_source
                or f'getattr(config, "{attribute}"' in modeling_source
                or f'getattr(self.config, "{attribute}"' in modeling_source
                or (
                    "TextConfig" in config_class.__name__
                    and f"config.get_text_config().{attribute}" in modeling_source
                )
            ):
                return True
            # Deal with multi-line cases
            elif (
                re.search(
                    rf'getattr[ \t\v\n\r\f]*\([ \t\v\n\r\f]*(self\.)?config,[ \t\v\n\r\f]*"{attribute}"',
                    modeling_source,
                )
                is not None
            ):
                return True

    # Special cases to be allowed even if not found as used
    for attribute in attributes:
        # Allow if the default value in the configuration class is different from the one in `PreTrainedConfig`
        if (attribute == "is_encoder_decoder" and default_value is True) or attribute == "tie_word_embeddings":
            return True
        # General exceptions for all models
        elif any(re.search(exception, attribute) for exception in ATTRIBUTES_TO_ALLOW):
            return True
        # Model-specific exceptions
        elif config_class.__name__ in SPECIAL_CASES_TO_ALLOW:
            model_exceptions = SPECIAL_CASES_TO_ALLOW[config_class.__name__]
            # Can be true to allow all attributes, or a list of specific allowed attributes
            if (isinstance(model_exceptions, bool) and model_exceptions) or attribute in model_exceptions:
                return True

    return False