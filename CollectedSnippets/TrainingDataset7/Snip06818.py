def as_sqlite(self, compiler, connection, **extra_context):
        function = None
        if self.geo_field.geodetic(connection):
            function = "GeodesicLength" if self.spheroid else "GreatCircleLength"
        return super().as_sql(compiler, connection, function=function, **extra_context)