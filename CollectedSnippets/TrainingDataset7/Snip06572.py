def get_geometry_converter(self, expression):
        raise NotImplementedError(
            "Subclasses of BaseSpatialOperations must provide a "
            "get_geometry_converter() method."
        )