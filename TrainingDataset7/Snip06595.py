def _create_spatial_index_name(self, model, field):
        return "%s_%s_id" % (model._meta.db_table, field.column)