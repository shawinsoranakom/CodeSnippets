def geo_db_type(self, f):
        """
        Return None because geometry columns are added via the
        `AddGeometryColumn` stored procedure on SpatiaLite.
        """
        return None