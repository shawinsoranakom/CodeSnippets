def get_geom_placeholder_sql(self, f, value, compiler):
        """
        Return the placeholder for the given geometry field with the given
        value. Depending on the spatial backend, the placeholder may contain a
        stored procedure call to the transformation function of the spatial
        backend.
        """
        if hasattr(value, "as_sql"):
            sql, params = compiler.compile(value)
            if self._must_transform_value(value.output_field, f):
                transform_func = self.spatial_function_name("Transform")
                sql = f"{transform_func}({sql}, %s)"
                params = (*params, f.srid)
            return sql, params
        elif self._must_transform_value(value, f):
            transform_func = self.spatial_function_name("Transform")
            sql = f"{transform_func}({self.from_text}(%s, %s), %s)"
            params = (value, value.srid, f.srid)
            return sql, params
        elif self.connection.features.has_spatialrefsys_table:
            return f"{self.from_text}(%s, %s)", (value, f.srid)
        else:
            # For backwards compatibility on MySQL (#27464).
            return f"{self.from_text}(%s)", (value,)