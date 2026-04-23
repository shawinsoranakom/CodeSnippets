def get_geom_placeholder_sql(self, f, value, compiler):
        """
        Provide a proper substitution value for Geometries or rasters that are
        not in the SRID of the field. Specifically, this routine will
        substitute in the ST_Transform() function call.
        """
        transform_func = self.spatial_function_name("Transform")
        if hasattr(value, "as_sql"):
            sql, params = compiler.compile(value)
            if value.field.srid != f.srid:
                sql = f"{transform_func}({sql}, %s)"
                params = (*params, f.srid)
            return sql, params

        # Get the srid for this object
        if value is None:
            value_srid = None
        else:
            value_srid = value.srid

        # Adding Transform() to the SQL placeholder if the value srid
        # is not equal to the field srid.
        if value_srid is None or value_srid == f.srid:
            return "%s", (value,)
        else:
            return f"{transform_func}(%s, %s)", (value, f.srid)