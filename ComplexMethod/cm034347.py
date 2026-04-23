def parse_scm(collection, version):
    """Extract name, version, path and subdir out of the SCM pointer."""
    if ',' in collection:
        collection, version = collection.split(',', 1)
    elif version == '*' or not version:
        version = 'HEAD'

    if collection.startswith('git+'):
        path = collection[4:]
    else:
        path = collection

    path, fragment = urldefrag(path)
    fragment = fragment.strip(os.path.sep)

    if path.endswith(os.path.sep + '.git'):
        name = path.split(os.path.sep)[-2]
    elif '://' not in path and '@' not in path:
        name = path
    else:
        name = path.split('/')[-1]
        if name.endswith('.git'):
            name = name[:-4]

    return name, version, path, fragment