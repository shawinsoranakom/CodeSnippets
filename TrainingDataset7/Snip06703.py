def _create_spatial_index_name(self, model, field):
        return self._create_index_name(model._meta.db_table, [field.column], "_id")