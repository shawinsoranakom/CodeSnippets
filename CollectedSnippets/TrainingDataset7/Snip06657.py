def get_field_type(self, data_type, description):
        if not self.postgis_oid_lookup:
            # Query PostgreSQL's pg_type table to determine the OID integers
            # for the PostGIS data types used in reverse lookup (the integers
            # may be different across versions). To prevent unnecessary
            # requests upon connection initialization, the `data_types_reverse`
            # dictionary isn't updated until introspection is performed here.
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT oid, typname "
                    "FROM pg_type "
                    "WHERE typname IN ('geometry', 'geography')"
                )
                self.postgis_oid_lookup = dict(cursor.fetchall())
            self.data_types_reverse.update(
                (oid, "GeometryField") for oid in self.postgis_oid_lookup
            )
        return super().get_field_type(data_type, description)