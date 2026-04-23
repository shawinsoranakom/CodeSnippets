def check_dict_alignment(
    base: dict, custom: dict, e: Exception | None = None, allowed_custom_keys: set | None = None
) -> None:
    """Check alignment between custom and base configuration dictionaries, handling deprecated keys and providing error
    messages for mismatched keys.

    Args:
        base (dict): The base configuration dictionary containing valid keys.
        custom (dict): The custom configuration dictionary to be checked for alignment.
        e (Exception | None): Optional error instance passed by the calling function.
        allowed_custom_keys (set | None): Optional set of additional keys that are allowed in the custom dictionary.

    Raises:
        SystemExit: If mismatched keys are found between the custom and base dictionaries.

    Examples:
        >>> base_cfg = {"epochs": 50, "lr0": 0.01, "batch_size": 16}
        >>> custom_cfg = {"epoch": 100, "lr": 0.02, "batch_size": 32}
        >>> try:
        ...     check_dict_alignment(base_cfg, custom_cfg)
        ... except SystemExit:
        ...     print("Mismatched keys found")

    Notes:
        - Suggests corrections for mismatched keys based on similarity to valid keys.
        - Automatically replaces deprecated keys in the custom configuration with updated equivalents.
        - Prints detailed error messages for each mismatched key to help users correct their configurations.
    """
    custom = _handle_deprecation(custom)
    base_keys, custom_keys = (frozenset(x.keys()) for x in (base, custom))
    # Allow 'augmentations' as a valid custom parameter for custom Albumentations transforms
    if allowed_custom_keys is None:
        allowed_custom_keys = {"augmentations", "save_dir"}
    if mismatched := [k for k in custom_keys if k not in base_keys and k not in allowed_custom_keys]:
        from difflib import get_close_matches

        string = ""
        for x in mismatched:
            matches = get_close_matches(x, base_keys)  # key list
            matches = [f"{k}={base[k]}" if base.get(k) is not None else k for k in matches]
            match_str = f"Similar arguments are i.e. {matches}." if matches else ""
            string += f"'{colorstr('red', 'bold', x)}' is not a valid YOLO argument. {match_str}\n"
        raise SyntaxError(string + CLI_HELP_MSG) from e