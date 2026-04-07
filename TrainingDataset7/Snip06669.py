def function_names(self):
        function_names = {
            "AsWKB": "ST_AsBinary",
            "AsWKT": "ST_AsText",
            "BoundingCircle": "ST_MinimumBoundingCircle",
            "FromWKB": "ST_GeomFromWKB",
            "FromWKT": "ST_GeomFromText",
            "NumDimensions": "ST_NDims",
            "NumPoints": "ST_NPoints",
            "GeometryType": "GeometryType",
        }
        return function_names