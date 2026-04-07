def as_sql(self, connection, lookup, template_params, *args):
        template_params = self.check_raster(lookup, template_params)
        template_params = self.check_geography(lookup, template_params)
        return super().as_sql(connection, lookup, template_params, *args)