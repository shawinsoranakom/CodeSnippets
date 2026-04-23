def postgis_version(self):
        "Return PostGIS version number and compile-time options."
        return self._get_postgis_func("postgis_version")