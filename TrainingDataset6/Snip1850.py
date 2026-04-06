def get_new_command(command):
    brew_cask_script = _get_script_for_brew_cask(command.output)
    return shell.and_(brew_cask_script, command.script)