def test_unique_with_deterministic_collation_charfield(self):
        deterministic_collation = connection.features.test_collations.get(
            "deterministic"
        )
        if not deterministic_collation:
            self.skipTest("This backend does not support deterministic collations.")

        class CharModel(Model):
            field = CharField(db_collation=deterministic_collation, unique=True)

            class Meta:
                app_label = "schema"

        # Create the table.
        with connection.schema_editor() as editor:
            editor.create_model(CharModel)
        self.isolated_local_models = [CharModel]
        constraints = self.get_constraints_for_column(
            CharModel, CharModel._meta.get_field("field").column
        )
        self.assertIn("schema_charmodel_field_8b338dea_like", constraints)
        self.assertIn(
            "varchar_pattern_ops",
            self.get_constraint_opclasses("schema_charmodel_field_8b338dea_like"),
        )
        self.assertEqual(
            self.get_column_collation(CharModel._meta.db_table, "field"),
            deterministic_collation,
        )
        self.assertIn("field", self.get_uniques(CharModel._meta.db_table))