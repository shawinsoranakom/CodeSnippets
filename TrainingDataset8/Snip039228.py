def create_script_finished_message(
    status: "ForwardMsg.ScriptFinishedStatus.ValueType",
) -> ForwardMsg:
    """Create a script_finished ForwardMsg."""
    msg = ForwardMsg()
    msg.script_finished = status
    return msg