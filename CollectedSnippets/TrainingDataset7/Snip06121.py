def _subclass_index(class_path, candidate_paths):
    """
    Return the index of dotted class path (or a subclass of that class) in a
    list of candidate paths. If it does not exist, return -1.
    """
    cls = import_string(class_path)
    for index, path in enumerate(candidate_paths):
        try:
            candidate_cls = import_string(path)
            if issubclass(candidate_cls, cls):
                return index
        except (ImportError, TypeError):
            continue
    return -1