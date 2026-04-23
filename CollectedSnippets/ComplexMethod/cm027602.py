def check_if_deprecated_constant(name: str, module_globals: dict[str, Any]) -> Any:
    """Check if the not found name is a deprecated constant.

    If it is, print a deprecation warning and return the value of the constant.
    Otherwise raise AttributeError.
    """
    module_name = module_globals.get("__name__")
    value = replacement = None
    description = "constant"
    if (deprecated_const := module_globals.get(_PREFIX_DEPRECATED + name)) is None:
        raise AttributeError(f"Module {module_name!r} has no attribute {name!r}")
    if isinstance(deprecated_const, DeprecatedConstant):
        value = deprecated_const.value
        replacement = deprecated_const.replacement
        breaks_in_ha_version = deprecated_const.breaks_in_ha_version
    elif isinstance(deprecated_const, DeprecatedConstantEnum):
        value = deprecated_const.enum
        replacement = (
            f"{deprecated_const.enum.__class__.__name__}.{deprecated_const.enum.name}"
        )
        breaks_in_ha_version = deprecated_const.breaks_in_ha_version
    elif isinstance(deprecated_const, (DeprecatedAlias, DeferredDeprecatedAlias)):
        description = "alias"
        value = deprecated_const.value
        replacement = deprecated_const.replacement
        breaks_in_ha_version = deprecated_const.breaks_in_ha_version

    if value is None or replacement is None:
        msg = (
            f"Value of {_PREFIX_DEPRECATED}{name} is an instance of "
            f"{type(deprecated_const)} but an instance of DeprecatedAlias, "
            "DeferredDeprecatedAlias, DeprecatedConstant or DeprecatedConstantEnum "
            "is required"
        )

        logging.getLogger(module_name).debug(msg)
        # PEP 562 -- Module __getattr__ and __dir__
        # specifies that __getattr__ should raise AttributeError if the attribute is not
        # found.
        # https://peps.python.org/pep-0562/#specification
        raise AttributeError(msg)

    _print_deprecation_warning_internal(
        name,
        module_name or __name__,
        replacement,
        description,
        "used",
        breaks_in_ha_version,
        log_when_no_integration_is_found=False,
    )
    return value