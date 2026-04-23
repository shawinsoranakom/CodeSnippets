def set_safe_mutable(dictionary, path, value):
    """
    Mutates original dict and sets the specified value under provided path.

    :type dictionary: dict
    :param dictionary: Dict to mutate.

    :type path: list|str
    :param path: List or dot-separated string containing the path of an attribute,
                 starting from the root node "$".

    :type value: any
    :param value: Value to set under specified path.

    :rtype: dict
    :return: Returns mutated dictionary.
    """
    if not isinstance(dictionary, dict):
        raise AttributeError('"dictionary" must be of type "dict"')

    attribute_path = path if isinstance(path, list) else path.split(".")
    attribute_path_len = len(attribute_path)

    if attribute_path_len == 0 or attribute_path[0] != "$":
        raise AttributeError('Dict navigation must begin with a root node "$"')

    current_pointer = dictionary
    for i in range(attribute_path_len):
        path_node = attribute_path[i]

        if path_node == "$":
            continue

        if i < attribute_path_len - 1:
            if path_node not in current_pointer:
                current_pointer[path_node] = {}
            if not isinstance(current_pointer, dict):
                raise RuntimeError(
                    'Error while deeply setting a dict value. Supplied path is not of type "dict"'
                )
        else:
            current_pointer[path_node] = value

        current_pointer = current_pointer[path_node]

    return dictionary