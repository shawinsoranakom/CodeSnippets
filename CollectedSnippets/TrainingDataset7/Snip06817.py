def as_postgresql(self, compiler, connection, **extra_context):
        clone = self.copy()
        function = None
        if self.source_is_geography():
            clone.source_expressions.append(Value(self.spheroid))
        elif self.geo_field.geodetic(connection):
            # Geometry fields with geodetic (lon/lat) coordinates need
            # length_spheroid
            function = connection.ops.spatial_function_name("LengthSpheroid")
            clone.source_expressions.append(Value(self.geo_field.spheroid(connection)))
        else:
            dim = min(f.dim for f in self.get_source_fields() if f)
            if dim > 2:
                function = connection.ops.length3d
        return super(Length, clone).as_sql(
            compiler, connection, function=function, **extra_context
        )