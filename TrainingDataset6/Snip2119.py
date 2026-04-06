def match(command):
    return (is_arg_url(command) or
            command.output.strip().startswith('The file ') and
            command.output.strip().endswith(' does not exist.'))