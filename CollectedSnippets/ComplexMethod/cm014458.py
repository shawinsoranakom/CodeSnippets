def _deprecation_warning(
    old_class_name: str,
    *,
    deprecation_version: str,
    removal_version: str,
    old_functional_name: str = "",
    old_argument_name: str = "",
    new_class_name: str = "",
    new_functional_name: str = "",
    new_argument_name: str = "",
    deprecate_functional_name_only: bool = False,
) -> None:
    if new_functional_name and not old_functional_name:
        raise ValueError(
            "Old functional API needs to be specified for the deprecation warning."
        )
    if new_argument_name and not old_argument_name:
        raise ValueError(
            "Old argument name needs to be specified for the deprecation warning."
        )

    if old_functional_name and old_argument_name:
        raise ValueError(
            "Deprecating warning for functional API and argument should be separated."
        )

    msg = f"`{old_class_name}()`"
    if deprecate_functional_name_only and old_functional_name:
        msg = f"{msg}'s functional API `.{old_functional_name}()` is"
    elif old_functional_name:
        msg = f"{msg} and its functional API `.{old_functional_name}()` are"
    elif old_argument_name:
        msg = f"The argument `{old_argument_name}` of {msg} is"
    else:
        msg = f"{msg} is"
    msg = (
        f"{msg} deprecated since {deprecation_version} and will be removed in {removal_version}."
        f"\nSee https://github.com/pytorch/data/issues/163 for details."
    )

    if new_class_name or new_functional_name:
        msg = f"{msg}\nPlease use"
        if new_class_name:
            msg = f"{msg} `{new_class_name}()`"
        if new_class_name and new_functional_name:
            msg = f"{msg} or"
        if new_functional_name:
            msg = f"{msg} `.{new_functional_name}()`"
        msg = f"{msg} instead."

    if new_argument_name:
        msg = f"{msg}\nPlease use `{old_class_name}({new_argument_name}=)` instead."

    warnings.warn(msg, FutureWarning, stacklevel=2)