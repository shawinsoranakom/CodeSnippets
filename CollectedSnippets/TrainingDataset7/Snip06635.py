def _create_spatial_index_name(self, model, field):
        # Oracle doesn't allow object names > 30 characters. Use this scheme
        # instead of self._create_index_name() for backwards compatibility.
        return truncate_name(
            "%s_%s_id" % (strip_quotes(model._meta.db_table), field.column), 30
        )