def match(command):
    return 'manage.py' in command.script and \
           'migrate' in command.script \
           and 'or pass --delete-ghost-migrations' in command.output