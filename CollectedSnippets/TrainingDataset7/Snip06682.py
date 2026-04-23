def postgis_version_tuple(self):
        """
        Return the PostGIS version as a tuple (version string, major,
        minor, subminor).
        """
        version = self.postgis_lib_version()
        return (version, *get_version_tuple(version))