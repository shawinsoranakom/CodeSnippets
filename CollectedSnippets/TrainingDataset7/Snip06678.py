def postgis_lib_version(self):
        """
        Return the version number of the PostGIS library used with PostgreSQL.
        """
        return self._get_postgis_func("postgis_lib_version")