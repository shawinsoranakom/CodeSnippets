def check_target_module_exists(optim_target_modules, key: str, return_is_regex: bool = False):
    """A helper method to check if the passed module's key name matches any of the target modules in the optim_target_modules.

    Args:
        optim_target_modules (`Union[str, list[str]]`):
            A list of strings to try to match. Can be also a full string.
        key (`str`):
            A key to search any matches in optim_target_modules
        return_is_regex (`bool`):
            If set to `True`, the method will return whether the passed `optim_target_modules`
            is a regex or not.

    Returns:
        `bool` : True of match object if key matches any target modules from config, False or
        None if no match found
        `bool` : If the matched target module is a regex to silence out the warnings in Trainer
        for extra modules being found (only if `target_module_found=True` for an array of regex).
    """
    target_module_found = False
    is_regex = False

    if isinstance(optim_target_modules, str):
        target_module_found = bool(re.fullmatch(optim_target_modules, key))
        is_regex = optim_target_modules != key
    elif key in optim_target_modules:  # from here, target_module_found must be a list of str
        # this module is specified directly in target_modules
        target_module_found = True
    elif any(target_key in key for target_key in optim_target_modules):
        target_module_found = True
    elif any(bool(re.fullmatch(optim_target_module, key)) for optim_target_module in optim_target_modules):
        target_module_found = True
        is_regex = True

    if return_is_regex:
        return target_module_found, is_regex

    return target_module_found