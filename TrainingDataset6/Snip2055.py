def get_new_command(command):
    apps = re.findall('([^ ]*) \\([^)]*\\)', command.output)
    return [command.script + ' --app ' + app for app in apps]