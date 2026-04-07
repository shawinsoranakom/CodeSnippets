def _delete_spatial_index_sql(self, model, field):
        index_name = self._create_spatial_index_name(model, field)
        return self._delete_index_sql(model, index_name)