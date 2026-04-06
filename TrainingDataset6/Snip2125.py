def match(command):
    return (command.script_parts
            and (command.script_parts[0] in ('pacman', 'yay', 'pikaur', 'yaourt')
                 or command.script_parts[0:2] == ['sudo', 'pacman'])
            and 'error: target not found:' in command.output)