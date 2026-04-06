def match(command):
    return (not which(command.script_parts[0])
            and ('not found' in command.output
                 or 'is not recognized as' in command.output)
            and bool(get_close_matches(command.script_parts[0],
                                       get_all_executables())))