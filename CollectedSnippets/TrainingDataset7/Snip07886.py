def register_type_handlers(connection, **kwargs):
        if connection.vendor != "postgresql" or connection.alias == NO_DB_ALIAS:
            return

        oids, array_oids = get_hstore_oids(connection.alias)
        for oid, array_oid in zip(oids, array_oids):
            ti = TypeInfo("hstore", oid, array_oid)
            hstore.register_hstore(ti, connection.connection)

        _, citext_oids = get_citext_oids(connection.alias)
        for array_oid in citext_oids:
            ti = TypeInfo("citext", 0, array_oid)
            ti.register(connection.connection)