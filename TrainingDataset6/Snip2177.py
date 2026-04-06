def get_new_command(command):
    if '&&' in command.script:
        return u'sudo sh -c "{}"'.format(" ".join([part for part in command.script_parts if part != "sudo"]))
    elif '>' in command.script:
        return u'sudo sh -c "{}"'.format(command.script.replace('"', '\\"'))
    else:
        return u'sudo {}'.format(command.script)