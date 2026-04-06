def get_new_command(command):
    url = re.findall(
        r'Visit ([^ ]*) for documentation about this command.',
        command.output)[0]

    return open_command(url)