def match(command):
    return re.search(error_pattern, command.output) or re.search(error_pattern2, command.output)