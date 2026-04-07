def __str__(self):
        return "%s.%s - %dD %s field (SRID: %d)" % (
            self.f_table_name,
            self.f_geometry_column,
            self.coord_dimension,
            self.type,
            self.srid,
        )