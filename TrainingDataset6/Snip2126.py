def get_new_command(command):
    pgr = command.script_parts[-1]

    return replace_command(command, pgr, get_pkgfile(pgr))