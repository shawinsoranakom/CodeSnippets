def _field_indexes_sql(self, model, field):
        if isinstance(field, GeometryField) and field.spatial_index:
            return [self._create_spatial_index_sql(model, field)]
        return super()._field_indexes_sql(model, field)