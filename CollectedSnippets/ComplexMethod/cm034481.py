def _recover_package_name(names):
    """Recover package names as list from user's raw input.

    :input: a mixed and invalid list of names or version specifiers
    :return: a list of valid package name

    eg.
    input: ['django>1.11.1', '<1.11.3', 'ipaddress', 'simpleproject>1.1.0', '<2.0.0']
    return: ['django>1.11.1,<1.11.3', 'ipaddress', 'simpleproject>1.1.0,<2.0.0']

    input: ['django>1.11.1,<1.11.3,ipaddress', 'simpleproject>1.1.0,<2.0.0']
    return: ['django>1.11.1,<1.11.3', 'ipaddress', 'simpleproject>1.1.0,<2.0.0']
    """
    # rebuild input name to a flat list so we can tolerate any combination of input
    tmp = []
    for one_line in names:
        tmp.extend(one_line.split(","))
    names = tmp

    # reconstruct the names
    name_parts = []
    package_names = []
    in_brackets = False
    for name in names:
        if _is_package_name(name) and not in_brackets:
            if name_parts:
                package_names.append(",".join(name_parts))
            name_parts = []
        if "[" in name:
            in_brackets = True
        if in_brackets and "]" in name:
            in_brackets = False
        name_parts.append(name)
    package_names.append(",".join(name_parts))
    return package_names