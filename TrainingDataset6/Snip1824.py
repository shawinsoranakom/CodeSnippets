def match(command):
    return (is_app(command, 'adb')
            and command.output.startswith('Android Debug Bridge version'))