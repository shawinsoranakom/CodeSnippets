def get_new_command(command):
    output = command.output.strip()
    if is_arg_url(command):
        yield command.script.replace('open ', 'open http://')
    elif output.startswith('The file ') and output.endswith(' does not exist.'):
        arg = command.script.split(' ', 1)[1]
        for option in ['touch', 'mkdir']:
            yield shell.and_(u'{} {}'.format(option, arg), command.script)