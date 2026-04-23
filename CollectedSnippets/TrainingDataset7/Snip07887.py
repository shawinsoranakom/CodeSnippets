def register_type_handlers(connection, **kwargs):
        if connection.vendor != "postgresql" or connection.alias == NO_DB_ALIAS:
            return

        oids, array_oids = get_hstore_oids(connection.alias)
        # Don't register handlers when hstore is not available on the database.
        #
        # If someone tries to create an hstore field it will error there. This
        # is necessary as someone may be using PSQL without extensions
        # installed but be using other features of contrib.postgres.
        #
        # This is also needed in order to create the connection in order to
        # install the hstore extension.
        if oids:
            register_hstore(
                connection.connection, globally=True, oid=oids, array_oid=array_oids
            )

        oids, citext_oids = get_citext_oids(connection.alias)
        # Don't register handlers when citext is not available on the database.
        #
        # The same comments in the above call to register_hstore() also apply
        # here.
        if oids:
            array_type = psycopg2.extensions.new_array_type(
                citext_oids, "citext[]", psycopg2.STRING
            )
            psycopg2.extensions.register_type(array_type, None)