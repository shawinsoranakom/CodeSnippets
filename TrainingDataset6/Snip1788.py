def _get_previous_command():
    history = shell.get_history()

    if history:
        return history[-1]
    else:
        return None