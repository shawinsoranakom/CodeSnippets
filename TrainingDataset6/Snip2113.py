def _get_available_commands(stdout):
    commands_listing = False
    for line in stdout.split('\n'):
        if line.startswith('where <command> is one of:'):
            commands_listing = True
        elif commands_listing:
            if not line:
                break

            for command in line.split(', '):
                stripped = command.strip()
                if stripped:
                    yield stripped