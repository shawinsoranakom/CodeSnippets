def get_hstore_oids(connection_alias):
    """Return hstore and hstore array OIDs."""
    return get_type_oids(connection_alias, "hstore")