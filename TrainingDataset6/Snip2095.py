def get_new_command(command):
    return [command.script + ' clean package',
            command.script + ' clean install']