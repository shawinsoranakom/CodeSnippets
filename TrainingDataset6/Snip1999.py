def _get_upstream_option_index(command_parts):
    if '--set-upstream' in command_parts:
        return command_parts.index('--set-upstream')
    elif '-u' in command_parts:
        return command_parts.index('-u')
    else:
        return None