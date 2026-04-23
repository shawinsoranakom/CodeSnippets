def get_citext_oids(connection_alias):
    """Return citext and citext array OIDs."""
    return get_type_oids(connection_alias, "citext")