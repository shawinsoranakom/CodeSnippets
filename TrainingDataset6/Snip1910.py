def match(command):
    return 'manage.py' in command.script and \
           'migrate' in command.script \
           and '--merge: will just attempt the migration' in command.output