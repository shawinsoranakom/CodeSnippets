def get_new_command(command):
    path = re.findall(
        r"touch: (?:cannot touch ')?(.+)/.+'?:", command.output)[0]
    return shell.and_(u'mkdir -p {}'.format(path), command.script)