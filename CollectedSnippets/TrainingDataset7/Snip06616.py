def get_geom_placeholder_sql(self, f, value, compiler):
        if value is None:
            return "NULL", ()
        return super().get_geom_placeholder_sql(f, value, compiler)