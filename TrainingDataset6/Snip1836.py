def _parse_apt_get_and_cache_operations(help_text_lines):
    is_commands_list = False
    for line in help_text_lines:
        line = line.decode().strip()
        if is_commands_list:
            if not line:
                return

            yield line.split()[0]
        elif line.startswith('Commands:') \
                or line.startswith('Most used commands:'):
            is_commands_list = True