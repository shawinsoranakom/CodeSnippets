def main():
    """Main entry point for standalone script execution."""

    if not HAS_DNF:
        _exit_json({'failed': True, 'msg': 'python3-dnf not found'})

    try:
        request = json.load(sys.stdin)
    except Exception as e:
        _exit_json({'failed': True, 'msg': f'Failed to read JSON input: {e}'})

    command = request.get('command')
    if not command:
        _exit_json({'failed': True, 'msg': 'No command specified'})

    config = request.get('config', {})
    params = request.get('params', {})

    if command == 'list':
        list_command = params.get('list_command')
        if not list_command:
            _exit_json({'failed': True, 'msg': 'No list_command specified for list operation'})
        result = list_items(config, list_command)

    elif command == 'ensure':
        result = ensure(config, params)

    elif command == 'update-cache':
        result = update_cache_only(config)

    else:
        _exit_json({'failed': True, 'msg': f'Unknown command: {command}'})

    _exit_json(result)