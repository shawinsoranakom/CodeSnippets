def find_deprecations(obj, path=None):
    if not isinstance(obj, (list, dict)):
        return

    try:
        items = obj.items()
    except AttributeError:
        items = enumerate(obj)

    for key, value in items:
        if path is None:
            this_path = []
        else:
            this_path = path[:]

        this_path.append(key)

        if key != 'deprecated':
            yield from find_deprecations(value, path=this_path)
        else:
            try:
                version = value['version']
                this_path.append('version')
            except KeyError:
                version = value['removed_in']
                this_path.append('removed_in')
            if StrictVersion(version) <= ANSIBLE_MAJOR:
                yield (this_path, version)