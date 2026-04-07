def postgis_proj_version(self):
        """Return the version of the PROJ library used with PostGIS."""
        return self._get_postgis_func("postgis_proj_version")