def get_new_command(command):
    name = regex.findall(command.output)[0]
    return shell.and_('nix-env -iA {}'.format(name), command.script)