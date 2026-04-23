def postgis_geos_version(self):
        "Return the version of the GEOS library used with PostGIS."
        return self._get_postgis_func("postgis_geos_version")