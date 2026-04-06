def get_new_command(command):
    broken_cmd = re.findall(r'tsuru: "([^"]*)" is not a tsuru command',
                            command.output)[0]
    return replace_command(command, broken_cmd,
                           get_all_matched_commands(command.output))