def match(command):
    return (command.script.startswith('./')
            and 'permission denied' in command.output.lower()
            and os.path.exists(command.script_parts[0])
            and not os.access(command.script_parts[0], os.X_OK))