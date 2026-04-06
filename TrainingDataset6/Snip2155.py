def match(command):
    return re.findall(r"Unrecognized command '.*'", command.output)