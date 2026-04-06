def _switch_command(command, layout):
    # Layouts with different amount of characters than English
    if layout in source_to_target:
        return ''.join(source_to_target[layout].get(ch, ch)
                       for ch in command.script)

    return ''.join(_switch(ch, layout) for ch in command.script)