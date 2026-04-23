def names_digest(*args, length):
    """
    Generate a 32-bit digest of a set of arguments that can be used to shorten
    identifying names.
    """
    h = md5(usedforsecurity=False)
    for arg in args:
        h.update(arg.encode())
    return h.hexdigest()[:length]