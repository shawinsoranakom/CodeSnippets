def get_new_command(command):
    misspelled_script = re.findall(
        r'.*missing script: (.*)\n', command.output)[0]
    return replace_command(command, misspelled_script, get_scripts())