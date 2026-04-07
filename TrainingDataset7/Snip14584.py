def contains(source, inst):
    """
    Return True if the "source" contains an instance of "inst". False,
    otherwise.
    """
    if isinstance(source, inst):
        return True
    if isinstance(source, NonCapture):
        for elt in source:
            if contains(elt, inst):
                return True
    return False