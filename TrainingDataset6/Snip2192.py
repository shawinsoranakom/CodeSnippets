def match(command):
    return re.search(MISTAKE, command.output) and re.search(FIX, command.output)