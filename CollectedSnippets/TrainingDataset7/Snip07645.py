def create_sql(self, model, schema_editor):
        return Statement(
            "ALTER TABLE %(table)s ADD %(constraint)s",
            table=Table(model._meta.db_table, schema_editor.quote_name),
            constraint=self.constraint_sql(model, schema_editor),
        )