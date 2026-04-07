def create_sql(self, model, schema_editor, using="gin", **kwargs):
                return super().create_sql(model, schema_editor, using=using, **kwargs)