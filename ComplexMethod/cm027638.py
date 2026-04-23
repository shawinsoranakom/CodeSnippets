async def trace_action(
    hass: HomeAssistant,
    script_run: _ScriptRun,
    stop: asyncio.Future[None],
    variables: TemplateVarsType,
) -> AsyncGenerator[TraceElement]:
    """Trace action execution."""
    path = trace_path_get()
    trace_element = action_trace_append(variables, path)
    trace_stack_push(trace_stack_cv, trace_element)

    trace_id = trace_id_get()
    if trace_id:
        key = trace_id[0]
        run_id = trace_id[1]
        breakpoints = hass.data[DATA_SCRIPT_BREAKPOINTS]
        if key in breakpoints and (
            (
                run_id in breakpoints[key]
                and (
                    path in breakpoints[key][run_id]
                    or NODE_ANY in breakpoints[key][run_id]
                )
            )
            or (
                RUN_ID_ANY in breakpoints[key]
                and (
                    path in breakpoints[key][RUN_ID_ANY]
                    or NODE_ANY in breakpoints[key][RUN_ID_ANY]
                )
            )
        ):
            async_dispatcher_send_internal(
                hass, SCRIPT_BREAKPOINT_HIT, key, run_id, path
            )

            done = hass.loop.create_future()

            @callback
            def async_continue_stop(
                command: Literal["continue", "stop"] | None = None,
            ) -> None:
                if command == "stop":
                    _set_result_unless_done(stop)
                _set_result_unless_done(done)

            signal = SCRIPT_DEBUG_CONTINUE_STOP.format(key, run_id)
            remove_signal1 = async_dispatcher_connect(hass, signal, async_continue_stop)
            remove_signal2 = async_dispatcher_connect(
                hass, SCRIPT_DEBUG_CONTINUE_ALL, async_continue_stop
            )

            await asyncio.wait([stop, done], return_when=asyncio.FIRST_COMPLETED)
            remove_signal1()
            remove_signal2()

    try:
        yield trace_element
    except _AbortScript as ex:
        trace_element.set_error(ex.__cause__ or ex)
        raise
    except _ConditionFail:
        # Clear errors which may have been set when evaluating the condition
        trace_element.set_error(None)
        raise
    except _StopScript:
        raise
    except Exception as ex:
        trace_element.set_error(ex)
        raise
    finally:
        trace_stack_pop(trace_stack_cv)