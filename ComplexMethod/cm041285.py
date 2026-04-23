def get_safe(dictionary, path, default_value=None):
    """
    Performs a safe navigation on a Dictionary object and
    returns the result or default value (if specified).
    The function follows a common AWS path resolution pattern "$.a.b.c".

    :type dictionary: dict
    :param dictionary: Dict to perform safe navigation.

    :type path: list|str
    :param path: List or dot-separated string containing the path of an attribute,
                 starting from the root node "$".

    :type default_value: any
    :param default_value: Default value to return in case resolved value is None.

    :rtype: any
    :return: Resolved value or default_value.
    """
    if not isinstance(dictionary, dict) or len(dictionary) == 0:
        return default_value

    attribute_path = path if isinstance(path, list) else path.split(".")
    if len(attribute_path) == 0 or attribute_path[0] != "$":
        raise AttributeError('Safe navigation must begin with a root node "$"')

    current_value = dictionary
    for path_node in attribute_path:
        if path_node == "$":
            continue

        if re.compile("^\\d+$").search(str(path_node)):
            path_node = int(path_node)

        if isinstance(current_value, dict) and path_node in current_value:
            current_value = current_value[path_node]
        elif isinstance(current_value, list) and path_node < len(current_value):
            current_value = current_value[path_node]
        else:
            current_value = None

    return current_value or default_value