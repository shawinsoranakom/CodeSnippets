def geo_db_type(self, f):
        """
        Return the geometry database type for Oracle. Unlike other spatial
        backends, no stored procedure is necessary and it's the same for all
        geometry types.
        """
        return "MDSYS.SDO_GEOMETRY"