def match(command):
    scm = command.script_parts[0]
    pattern = wrong_scm_patterns[scm]

    return pattern in command.output and _get_actual_scm()