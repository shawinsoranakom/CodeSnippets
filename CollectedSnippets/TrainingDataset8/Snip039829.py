def _is_control_event(event: ScriptRunnerEvent) -> bool:
    """True if the given ScriptRunnerEvent is a 'control' event, as opposed
    to a 'data' event.
    """
    # There's only one data event type.
    return event != ScriptRunnerEvent.ENQUEUE_FORWARD_MSG