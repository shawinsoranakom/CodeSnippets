def as_postgresql(self, compiler, connection, **extra_context):
        clone = self.copy()
        function = None
        expr2 = clone.source_expressions[1]
        geography = self.source_is_geography()
        if expr2.output_field.geography != geography:
            if isinstance(expr2, Value):
                expr2.output_field.geography = geography
            else:
                clone.source_expressions[1] = Cast(
                    expr2,
                    GeometryField(srid=expr2.output_field.srid, geography=geography),
                )

        if not geography and self.geo_field.geodetic(connection):
            # Geometry fields with geodetic (lon/lat) coordinates need special
            # distance functions.
            if self.spheroid:
                # DistanceSpheroid is more accurate and resource intensive than
                # DistanceSphere.
                function = connection.ops.spatial_function_name("DistanceSpheroid")
                # Replace boolean param by the real spheroid of the base field
                clone.source_expressions.append(
                    Value(self.geo_field.spheroid(connection))
                )
            else:
                function = connection.ops.spatial_function_name("DistanceSphere")
        return super(Distance, clone).as_sql(
            compiler, connection, function=function, **extra_context
        )