def get_new_command(command):
    return u'./gradlew {}'.format(' '.join(command.script_parts[1:]))