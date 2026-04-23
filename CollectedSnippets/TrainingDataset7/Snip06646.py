def __init__(self, *args, **kwargs):
        if kwargs.get("alias", "") == NO_DB_ALIAS:
            # Don't initialize PostGIS-specific stuff for non-db connections.
            self.features_class = PsycopgDatabaseFeatures
            self.ops_class = PsycopgDatabaseOperations
            self.introspection_class = PsycopgDatabaseIntrospection

        super().__init__(*args, **kwargs)