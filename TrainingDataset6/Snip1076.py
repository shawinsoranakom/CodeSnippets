def composer_not_command():
    # that weird spacing is part of the actual command output
    return (
        '\n'
        '\n'
        '                                    \n'
        '  [InvalidArgumentException]        \n'
        '  Command "udpate" is not defined.  \n'
        '  Did you mean this?                \n'
        '      update                        \n'
        '                                    \n'
        '\n'
        '\n'
    )