def get_new_command(command):
    if 'Usage:' in command.output and len(command.script_parts) > 1:
        management_subcommands = _parse_commands(command.output.split('\n'), 'Commands:')
        return replace_command(command, command.script_parts[2], management_subcommands)

    wrong_command = re.findall(
        r"docker: '(\w+)' is not a docker command.", command.output)[0]
    return replace_command(command, wrong_command, get_docker_commands())