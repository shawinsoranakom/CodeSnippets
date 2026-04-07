def get_col(self, alias, output_field=None):
        if alias == self.model._meta.db_table and (
            output_field is None or output_field == self
        ):
            return self.cached_col
        from django.db.models.expressions import Col

        return Col(alias, self, output_field)