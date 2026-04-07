def geometry_columns(self):
        raise NotImplementedError(
            "Subclasses of BaseSpatialOperations must provide a geometry_columns() "
            "method."
        )