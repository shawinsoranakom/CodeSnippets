def get_new_command(command):
    migration_script = re.search(SUGGESTION_REGEX, command.output).group(1)
    return shell.and_(migration_script, command.script)