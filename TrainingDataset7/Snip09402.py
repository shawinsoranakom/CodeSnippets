def _create_on_delete_sql(self, model, field):
        remote_field = field.remote_field
        try:
            return remote_field.on_delete.on_delete_sql(self)
        except AttributeError:
            return ""