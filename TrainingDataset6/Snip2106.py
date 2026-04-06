def get_new_command(command):
    for pattern in patterns:
        file = re.findall(pattern, command.output)

        if file:
            file = file[0]
            dir = file[0:file.rfind('/')]

            formatme = shell.and_('mkdir -p {}', '{}')
            return formatme.format(dir, command.script)