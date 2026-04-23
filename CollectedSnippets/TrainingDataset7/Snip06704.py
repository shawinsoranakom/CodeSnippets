def _create_spatial_index_sql(self, model, field, **kwargs):
        expressions = None
        opclasses = None
        fields = [field]
        if field.geom_type == "RASTER":
            # For raster fields, wrap index creation SQL statement with
            # ST_ConvexHull. Indexes on raster columns are based on the convex
            # hull of the raster.
            expressions = Func(Col(None, field), template=self.rast_index_template)
            fields = None
        elif field.dim > 2 and not field.geography:
            # Use "nd" ops which are fast on multidimensional cases
            opclasses = [self.geom_index_ops_nd]
        if not (name := kwargs.get("name")):
            name = self._create_spatial_index_name(model, field)

        return super()._create_index_sql(
            model,
            fields=fields,
            name=name,
            using=" USING %s" % self.geom_index_type,
            opclasses=opclasses,
            expressions=expressions,
        )