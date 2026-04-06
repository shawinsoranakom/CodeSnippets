def get_new_command(command):
    failed_lifecycle = _get_failed_lifecycle(command)
    available_lifecycles = _getavailable_lifecycles(command)
    if available_lifecycles and failed_lifecycle:
        selected_lifecycle = get_close_matches(
            failed_lifecycle.group(1), available_lifecycles.group(1).split(", "))
        return replace_command(command, failed_lifecycle.group(1), selected_lifecycle)
    else:
        return []