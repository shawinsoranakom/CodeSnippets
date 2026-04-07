def spatial_version(self):
        """Determine the version of the SpatiaLite library."""
        try:
            version = self.spatialite_version_tuple()[1:]
        except Exception as exc:
            raise ImproperlyConfigured(
                'Cannot determine the SpatiaLite version for the "%s" database. '
                "Was the SpatiaLite initialization SQL loaded on this database?"
                % (self.connection.settings_dict["NAME"],)
            ) from exc
        if version < (4, 3, 0):
            raise ImproperlyConfigured("GeoDjango supports SpatiaLite 4.3.0 and above.")
        return version