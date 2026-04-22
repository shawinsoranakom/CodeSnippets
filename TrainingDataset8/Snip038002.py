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