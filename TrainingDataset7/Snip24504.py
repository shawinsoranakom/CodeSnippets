def get_ogr_db_string():
    """
    Construct the DB string that GDAL will use to inspect the database.
    GDAL will create its own connection to the database, so we re-use the
    connection settings from the Django test.
    """
    db = connections.settings["default"]

    # Map from the django backend into the OGR driver name and database
    # identifier https://gdal.org/drivers/vector/
    #
    # TODO: Support Oracle (OCI).
    drivers = {
        "django.contrib.gis.db.backends.postgis": (
            "PostgreSQL",
            "PG:dbname='%(db_name)s'",
            " ",
        ),
        "django.contrib.gis.db.backends.mysql": ("MySQL", 'MYSQL:"%(db_name)s"', ","),
        "django.contrib.gis.db.backends.spatialite": ("SQLite", "%(db_name)s", ""),
    }

    db_engine = db["ENGINE"]
    if db_engine not in drivers:
        return None

    drv_name, db_str, param_sep = drivers[db_engine]

    # Ensure that GDAL library has driver support for the database.
    try:
        Driver(drv_name)
    except GDALException:
        return None

    # SQLite/SpatiaLite in-memory databases
    if DatabaseCreation.is_in_memory_db(db["NAME"]):
        return None

    # Build the params of the OGR database connection string
    params = [db_str % {"db_name": db["NAME"]}]

    def add(key, template):
        value = db.get(key, None)
        # Don't add the parameter if it is not in django's settings
        if value:
            params.append(template % value)

    add("HOST", "host='%s'")
    add("PORT", "port='%s'")
    add("USER", "user='%s'")
    add("PASSWORD", "password='%s'")

    return param_sep.join(params)