def feature_kwargs(self, feat):
        """
        Given an OGR Feature, return a dictionary of keyword arguments for
        constructing the mapped model.
        """
        # The keyword arguments for model construction.
        kwargs = {}

        # Incrementing through each model field and OGR field in the
        # dictionary mapping.
        for field_name, ogr_name in self.mapping.items():
            model_field = self.fields[field_name]

            if isinstance(model_field, GeometryField):
                # Verify OGR geometry.
                try:
                    val = self.verify_geom(feat.geom, model_field)
                except GDALException:
                    raise LayerMapError("Could not retrieve geometry from feature.")
            elif isinstance(model_field, models.base.ModelBase):
                # The related _model_, not a field was passed in -- indicating
                # another mapping for the related Model.
                val = self.verify_fk(feat, model_field, ogr_name)
            else:
                # Otherwise, verify OGR Field type.
                val = self.verify_ogr_field(feat[ogr_name], model_field)

            # Setting the keyword arguments for the field name with the
            # value obtained above.
            kwargs[field_name] = val

        return kwargs