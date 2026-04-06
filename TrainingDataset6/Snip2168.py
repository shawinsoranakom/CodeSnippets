def get_new_command(command):
    scm = _get_actual_scm()
    return u' '.join([scm] + command.script_parts[1:])