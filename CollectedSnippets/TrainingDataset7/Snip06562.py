def geo_db_type(self, f):
        """
        Return the database column type for the geometry field on
        the spatial backend.
        """
        raise NotImplementedError(
            "subclasses of BaseSpatialOperations must provide a geo_db_type() method"
        )