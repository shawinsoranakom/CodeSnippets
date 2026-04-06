def get_new_command(command):
    return u'{} -d {}'.format(
        command.script, shell.quote(_zip_file(command)[:-4]))