def composer_not_command_one_of_this():
    # that weird spacing is part of the actual command output
    return (
        '\n'
        '\n'
        '                                   \n'
        '  [InvalidArgumentException]       \n'
        '  Command "pdate" is not defined.  \n'
        '  Did you mean one of these?       \n'
        '      selfupdate                   \n'
        '      self-update                  \n'
        '      update                       \n'
        '                                   \n'
        '\n'
        '\n'
    )