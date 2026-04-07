def get_script_prefix(scope):
    """
    Return the script prefix to use from either the scope or a setting.
    """
    if settings.FORCE_SCRIPT_NAME:
        return settings.FORCE_SCRIPT_NAME
    return scope.get("root_path", "") or ""