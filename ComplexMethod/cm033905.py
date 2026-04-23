def subelements(obj, subelements, skip_missing=False):
    """Accepts a dict or list of dicts, and a dotted accessor and produces a product
    of the element and the results of the dotted accessor

    >>> obj = [{"name": "alice", "groups": ["wheel"], "authorized": ["/tmp/alice/onekey.pub"]}]
    >>> subelements(obj, 'groups')
    [({'name': 'alice', 'groups': ['wheel'], 'authorized': ['/tmp/alice/onekey.pub']}, 'wheel')]

    """
    if isinstance(obj, dict):
        element_list = list(obj.values())
    elif isinstance(obj, list):
        element_list = obj[:]
    else:
        raise AnsibleFilterError('obj must be a list of dicts or a nested dict')

    if isinstance(subelements, list):
        subelement_list = subelements[:]
    elif isinstance(subelements, str):
        subelement_list = subelements.split('.')
    else:
        raise AnsibleTypeError('subelements must be a list or a string')

    results = []

    for element in element_list:
        values = element
        for subelement in subelement_list:
            try:
                values = values[subelement]
            except KeyError:
                if skip_missing:
                    values = []
                    break
                raise AnsibleFilterError("could not find %r key in iterated item %r" % (subelement, values))
            except TypeError as ex:
                raise AnsibleTypeError("the key %s should point to a dictionary, got '%s'" % (subelement, values)) from ex
        if not isinstance(values, list):
            raise AnsibleTypeError("the key %r should point to a list, got %r" % (subelement, values))

        for value in values:
            results.append((element, value))

    return results