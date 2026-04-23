def test_non_db_connection_classes(self):
        from django.contrib.gis.db.backends.postgis.base import DatabaseWrapper
        from django.db.backends.postgresql.features import DatabaseFeatures
        from django.db.backends.postgresql.introspection import DatabaseIntrospection
        from django.db.backends.postgresql.operations import DatabaseOperations

        wrapper = DatabaseWrapper(settings_dict={}, alias=NO_DB_ALIAS)
        # PostGIS-specific stuff is not initialized for non-db connections.
        self.assertIs(wrapper.features_class, DatabaseFeatures)
        self.assertIs(wrapper.ops_class, DatabaseOperations)
        self.assertIs(wrapper.introspection_class, DatabaseIntrospection)