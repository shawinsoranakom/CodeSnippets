def test_relation_to_collation_charfield(self):
        ci_collation = self._add_ci_collation()

        class CiCharModel(Model):
            field = CharField(max_length=16, db_collation=ci_collation, unique=True)

            class Meta:
                app_label = "schema"

        class RelationModel(Model):
            field = OneToOneField(CiCharModel, CASCADE, to_field="field")

            class Meta:
                app_label = "schema"

        # Create the table.
        with connection.schema_editor() as editor:
            editor.create_model(CiCharModel)
            editor.create_model(RelationModel)
        self.isolated_local_models = [CiCharModel, RelationModel]
        self.assertEqual(
            self.get_column_collation(RelationModel._meta.db_table, "field_id"),
            ci_collation,
        )
        self.assertEqual(
            self.get_column_collation(CiCharModel._meta.db_table, "field"),
            ci_collation,
        )
        self.assertIn("field_id", self.get_uniques(RelationModel._meta.db_table))