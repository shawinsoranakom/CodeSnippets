def match(command):
    return ('did not match any file(s) known to git.' in command.output
            and _get_missing_file(command))