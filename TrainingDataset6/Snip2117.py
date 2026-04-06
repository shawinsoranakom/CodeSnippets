def get_new_command(command):
    broken = re.findall(r"env: no such command ['`]([^']*)'", command.output)[0]
    matched = [replace_argument(command.script, broken, common_typo)
               for common_typo in COMMON_TYPOS.get(broken, [])]

    app = command.script_parts[0]
    app_commands = cache(which(app))(get_app_commands)(app)
    matched.extend(replace_command(command, broken, app_commands))
    return matched