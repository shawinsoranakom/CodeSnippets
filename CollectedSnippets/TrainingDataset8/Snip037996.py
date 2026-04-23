def gather_metrics(name: str, func: Optional[F] = None) -> Union[Callable[[F], F], F]:
    """Function decorator to add telemetry tracking to commands.

    Parameters
    ----------
    func : callable
    The function to track for telemetry.

    name : str or None
    Overwrite the function name with a custom name that is used for telemetry tracking.

    Example
    -------
    >>> @st.gather_metrics
    ... def my_command(url):
    ...     return url

    >>> @st.gather_metrics(name="custom_name")
    ... def my_command(url):
    ...     return url
    """

    if not name:
        _LOGGER.warning("gather_metrics: name is empty")
        name = "undefined"

    if func is None:
        # Support passing the params via function decorator
        def wrapper(f: F) -> F:
            return gather_metrics(
                name=name,
                func=f,
            )

        return wrapper
    else:
        # To make mypy type narrow Optional[F] -> F
        non_optional_func = func

    @wraps(non_optional_func)
    def wrapped_func(*args, **kwargs):
        exec_start = timer()
        # get_script_run_ctx gets imported here to prevent circular dependencies
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        ctx = get_script_run_ctx()

        tracking_activated = (
            ctx is not None
            and ctx.gather_usage_stats
            and not ctx.command_tracking_deactivated
            and len(ctx.tracked_commands)
            < _MAX_TRACKED_COMMANDS  # Prevent too much memory usage
        )
        command_telemetry: Optional[Command] = None

        if ctx and tracking_activated:
            try:
                command_telemetry = _get_command_telemetry(
                    non_optional_func, name, *args, **kwargs
                )

                if (
                    command_telemetry.name not in ctx.tracked_commands_counter
                    or ctx.tracked_commands_counter[command_telemetry.name]
                    < _MAX_TRACKED_PER_COMMAND
                ):
                    ctx.tracked_commands.append(command_telemetry)
                ctx.tracked_commands_counter.update([command_telemetry.name])
                # Deactivate tracking to prevent calls inside already tracked commands
                ctx.command_tracking_deactivated = True
            except Exception as ex:
                # Always capture all exceptions since we want to make sure that
                # the telemetry never causes any issues.
                _LOGGER.debug("Failed to collect command telemetry", exc_info=ex)
        try:
            result = non_optional_func(*args, **kwargs)
        finally:
            # Activate tracking again if command executes without any exceptions
            if ctx:
                ctx.command_tracking_deactivated = False

        if tracking_activated and command_telemetry:
            # Set the execution time to the measured value
            command_telemetry.time = to_microseconds(timer() - exec_start)
        return result

    with contextlib.suppress(AttributeError):
        # Make this a well-behaved decorator by preserving important function
        # attributes.
        wrapped_func.__dict__.update(non_optional_func.__dict__)
        wrapped_func.__signature__ = inspect.signature(non_optional_func)  # type: ignore
    return cast(F, wrapped_func)