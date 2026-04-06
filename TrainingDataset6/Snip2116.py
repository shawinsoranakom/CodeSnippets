def get_app_commands(app):
    proc = Popen([app, 'commands'], stdout=PIPE)
    return [line.decode('utf-8').strip() for line in proc.stdout.readlines()]