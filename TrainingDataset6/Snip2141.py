def _is_recursive(part):
    if part == '--recurse':
        return True
    elif not part.startswith('--') and part.startswith('-') and 'r' in part:
        return True