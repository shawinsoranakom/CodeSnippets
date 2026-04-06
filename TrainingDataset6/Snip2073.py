def _get_destination(script_parts):
    """When arguments order is wrong first argument will be destination."""
    for part in script_parts:
        if part not in {'ln', '-s', '--symbolic'} and os.path.exists(part):
            return part