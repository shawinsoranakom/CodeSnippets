def execute(
    hass: HomeAssistant,
    filename: str,
    source: Any,
    data: dict[str, Any] | None = None,
    return_response: bool = False,
) -> dict | None:
    """Execute Python source."""

    compiled = compile_restricted_exec(source, filename=filename)

    if compiled.errors:
        _LOGGER.error(
            "Error loading script %s: %s", filename, ", ".join(compiled.errors)
        )
        return None

    if compiled.warnings:
        _LOGGER.warning(
            "Warning loading script %s: %s", filename, ", ".join(compiled.warnings)
        )

    def protected_getattr(obj: object, name: str, default: Any = None) -> Any:
        """Restricted method to get attributes."""
        if name.startswith("async_"):
            raise ScriptError("Not allowed to access async methods")
        if (
            (obj is hass and name not in ALLOWED_HASS)
            or (obj is hass.bus and name not in ALLOWED_EVENTBUS)
            or (obj is hass.states and name not in ALLOWED_STATEMACHINE)
            or (obj is hass.services and name not in ALLOWED_SERVICEREGISTRY)
            or (obj is dt_util and name not in ALLOWED_DT_UTIL)
            or (obj is datetime and name not in ALLOWED_DATETIME)
            or (isinstance(obj, TimeWrapper) and name not in ALLOWED_TIME)
        ):
            raise ScriptError(f"Not allowed to access {obj.__class__.__name__}.{name}")

        return getattr(obj, name, default)

    extra_builtins = {
        "__import__": guarded_import,
        "datetime": datetime,
        "sorted": sorted,
        "time": TimeWrapper(),
        "dt_util": dt_util,
        "min": min,
        "max": max,
        "sum": sum,
        "any": any,
        "all": all,
        "enumerate": enumerate,
    }
    builtins = safe_builtins.copy()
    builtins.update(utility_builtins)
    builtins.update(limited_builtins)
    builtins.update(extra_builtins)
    logger = logging.getLogger(f"{__name__}.{filename}")
    restricted_globals = {
        "__builtins__": builtins,
        "_print_": StubPrinter,
        "_getattr_": protected_getattr,
        "_write_": full_write_guard,
        "_getiter_": iter,
        "_getitem_": default_guarded_getitem,
        "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
        "_unpack_sequence_": guarded_unpack_sequence,
        "_inplacevar_": guarded_inplacevar,
        "hass": hass,
        "data": data or {},
        "logger": logger,
        "output": {},
    }

    try:
        _LOGGER.info("Executing %s: %s", filename, data)
        # pylint: disable-next=exec-used
        exec(compiled.code, restricted_globals)  # noqa: S102
        _LOGGER.debug(
            "Output of python_script: `%s`:\n%s",
            filename,
            restricted_globals["output"],
        )
        # Ensure that we're always returning a dictionary
        if not isinstance(restricted_globals["output"], dict):
            output_type = type(restricted_globals["output"])
            restricted_globals["output"] = {}
            raise ScriptError(  # noqa: TRY301
                f"Expected `output` to be a dictionary, was {output_type}"
            )
    except ScriptError as err:
        if return_response:
            raise ServiceValidationError(f"Error executing script: {err}") from err
        logger.error("Error executing script: %s", err)
        return None
    except Exception as err:
        if return_response:
            raise HomeAssistantError(
                f"Error executing script ({type(err).__name__}): {err}"
            ) from err
        logger.exception("Error executing script")
        return None

    return restricted_globals["output"]