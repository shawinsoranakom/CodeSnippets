def test_db_collation_arrayfield(self):
        from django.contrib.postgres.fields import ArrayField

        ci_collation = self._add_ci_collation()
        cs_collation = "en-x-icu"

        class ArrayModel(Model):
            field = ArrayField(CharField(max_length=16, db_collation=ci_collation))

            class Meta:
                app_label = "schema"

        # Create the table.
        with connection.schema_editor() as editor:
            editor.create_model(ArrayModel)
        self.isolated_local_models = [ArrayModel]
        self.assertEqual(
            self.get_column_collation(ArrayModel._meta.db_table, "field"),
            ci_collation,
        )
        # Alter collation.
        old_field = ArrayModel._meta.get_field("field")
        new_field_cs = ArrayField(CharField(max_length=16, db_collation=cs_collation))
        new_field_cs.set_attributes_from_name("field")
        new_field_cs.model = ArrayField
        with connection.schema_editor() as editor:
            editor.alter_field(ArrayModel, old_field, new_field_cs, strict=True)
        self.assertEqual(
            self.get_column_collation(ArrayModel._meta.db_table, "field"),
            cs_collation,
        )