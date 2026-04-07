def gis_operators(self):
        operators = {
            "bbcontains": SpatialOperator(
                func="MBRContains"
            ),  # For consistency w/PostGIS API
            "bboverlaps": SpatialOperator(func="MBROverlaps"),  # ...
            "contained": SpatialOperator(func="MBRWithin"),  # ...
            "contains": SpatialOperator(func="ST_Contains"),
            "coveredby": SpatialOperator(func="MBRCoveredBy"),
            "crosses": SpatialOperator(func="ST_Crosses"),
            "disjoint": SpatialOperator(func="ST_Disjoint"),
            "equals": SpatialOperator(func="ST_Equals"),
            "exact": SpatialOperator(func="ST_Equals"),
            "intersects": SpatialOperator(func="ST_Intersects"),
            "overlaps": SpatialOperator(func="ST_Overlaps"),
            "same_as": SpatialOperator(func="ST_Equals"),
            "touches": SpatialOperator(func="ST_Touches"),
            "within": SpatialOperator(func="ST_Within"),
        }
        if self.connection.mysql_is_mariadb:
            operators["relate"] = SpatialOperator(func="ST_Relate")
            if self.connection.mysql_version < (12, 0, 1):
                del operators["coveredby"]
        else:
            operators["covers"] = SpatialOperator(func="MBRCovers")
        return operators