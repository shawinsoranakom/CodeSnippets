def get_new_command(command):
    misspelled_env = command.script_parts[1]
    create_new = u'mkvirtualenv {}'.format(misspelled_env)

    available = _get_all_environments()
    if available:
        return (replace_command(command, misspelled_env, available)
                + [create_new])
    else:
        return create_new