def get_new_command(command):
    url = command.script_parts[1]

    if '/' in command.script:
        return 'whois ' + urlparse(url).netloc
    elif '.' in command.script:
        path = urlparse(url).path.split('.')
        return ['whois ' + '.'.join(path[n:]) for n in range(1, len(path))]