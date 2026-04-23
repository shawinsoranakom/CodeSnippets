def spatial_version(self):
        """Determine the version of the PostGIS library."""
        # Trying to get the PostGIS version because the function
        # signatures will depend on the version used. The cost
        # here is a database query to determine the version, which
        # can be mitigated by setting `POSTGIS_VERSION` with a 3-tuple
        # comprising user-supplied values for the major, minor, and
        # subminor revision of PostGIS.
        if hasattr(settings, "POSTGIS_VERSION"):
            version = settings.POSTGIS_VERSION
        else:
            # Run a basic query to check the status of the connection so we're
            # sure we only raise the error below if the problem comes from
            # PostGIS and not from PostgreSQL itself (see #24862).
            self._get_postgis_func("version")

            try:
                vtup = self.postgis_version_tuple()
            except ProgrammingError:
                raise ImproperlyConfigured(
                    'Cannot determine PostGIS version for database "%s" '
                    'using command "SELECT postgis_lib_version()". '
                    "GeoDjango requires at least PostGIS version 3.2. "
                    "Was the database created from a spatial database "
                    "template?" % self.connection.settings_dict["NAME"]
                )
            version = vtup[1:]
        return version