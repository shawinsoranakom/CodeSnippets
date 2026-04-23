def psycopg_version():
    version = Database.__version__.split(" ", 1)[0]
    return get_version_tuple(version)