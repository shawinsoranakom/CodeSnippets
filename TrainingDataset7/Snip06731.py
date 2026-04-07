def spatialite_version_tuple(self):
        """
        Return the SpatiaLite version as a tuple (version string, major,
        minor, subminor).
        """
        version = self.spatialite_version()
        return (version, *get_version_tuple(version))