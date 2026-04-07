def as_postgresql(self, compiler, connection, **extra_context):
        function = None
        if self.geo_field.geodetic(connection) and not self.source_is_geography():
            raise NotSupportedError(
                "ST_Perimeter cannot use a non-projected non-geography field."
            )
        dim = min(f.dim for f in self.get_source_fields())
        if dim > 2:
            function = connection.ops.perimeter3d
        return super().as_sql(compiler, connection, function=function, **extra_context)