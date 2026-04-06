def match(command):
    for pattern in patterns:
        if re.search(pattern, command.output):
            return True

    return False