def get_col(self, alias, output_field=None):
        if alias != self.model._meta.db_table and output_field in (None, self):
            output_field = self.output_field
        return super().get_col(alias, output_field)