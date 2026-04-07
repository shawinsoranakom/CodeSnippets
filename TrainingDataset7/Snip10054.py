def split_identifier(identifier):
    """
    Split an SQL identifier into a two element tuple of (namespace, name).

    The identifier could be a table, column, or sequence name might be prefixed
    by a namespace.
    """
    try:
        namespace, name = identifier.split('"."')
    except ValueError:
        namespace, name = "", identifier
    return namespace.strip('"'), name.strip('"')