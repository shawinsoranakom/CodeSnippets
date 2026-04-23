def get_from_dict_or_env(
    data: dict[str, Any],
    key: str | list[str],
    env_key: str,
    default: str | None = None,
) -> str:
    """Get a value from a dictionary or an environment variable.

    Args:
        data: The dictionary to look up the key in.
        key: The key to look up in the dictionary.

            This can be a list of keys to try in order.
        env_key: The environment variable to look up if the key is not
            in the dictionary.
        default: The default value to return if the key is not in the dictionary
            or the environment.

    Returns:
        The dict value or the environment variable value.
    """
    if isinstance(key, (list, tuple)):
        for k in key:
            if value := data.get(k):
                return str(value)

    if isinstance(key, str) and key in data and data[key]:
        return str(data[key])

    key_for_err = key[0] if isinstance(key, (list, tuple)) else key

    return get_from_env(key_for_err, env_key, default=default)