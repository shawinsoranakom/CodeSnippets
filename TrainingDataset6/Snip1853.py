def get_new_command(command):
    matcher = re.search('Warning: No available formula with the name "(?:[^"]+)". Did you mean (.+)\\?', command.output)
    suggestions = _get_suggestions(matcher.group(1))
    return ["brew install " + formula for formula in suggestions]