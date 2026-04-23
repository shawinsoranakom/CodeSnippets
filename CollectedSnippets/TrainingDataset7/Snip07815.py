def remove_collation(self, schema_editor):
        schema_editor.execute(
            "DROP COLLATION %s" % schema_editor.quote_name(self.name),
        )