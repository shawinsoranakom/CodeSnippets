def _create_script_finished_msg(status) -> ForwardMsg:
    msg = ForwardMsg()
    msg.script_finished = status
    return msg