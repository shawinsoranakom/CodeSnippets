def test_relation_to_deterministic_collation_charfield(self):
        deterministic_collation = connection.features.test_collations.get(
            "deterministic"
        )
        if not deterministic_collation:
            self.skipTest("This backend does not support deterministic collations.")

        class CharModel(Model):
            field = CharField(db_collation=deterministic_collation, unique=True)

            class Meta:
                app_label = "schema"

        class RelationModel(Model):
            field = OneToOneField(CharModel, CASCADE, to_field="field")

            class Meta:
                app_label = "schema"

        # Create the table.
        with connection.schema_editor() as editor:
            editor.create_model(CharModel)
            editor.create_model(RelationModel)
        self.isolated_local_models = [CharModel, RelationModel]
        constraints = self.get_constraints_for_column(
            CharModel, CharModel._meta.get_field("field").column
        )
        self.assertIn("schema_charmodel_field_8b338dea_like", constraints)
        self.assertIn(
            "varchar_pattern_ops",
            self.get_constraint_opclasses("schema_charmodel_field_8b338dea_like"),
        )
        rel_constraints = self.get_constraints_for_column(
            RelationModel, RelationModel._meta.get_field("field").column
        )
        self.assertIn("schema_relationmodel_field_id_395fbb08_like", rel_constraints)
        self.assertIn(
            "varchar_pattern_ops",
            self.get_constraint_opclasses(
                "schema_relationmodel_field_id_395fbb08_like"
            ),
        )
        self.assertEqual(
            self.get_column_collation(RelationModel._meta.db_table, "field_id"),
            deterministic_collation,
        )
        self.assertEqual(
            self.get_column_collation(CharModel._meta.db_table, "field"),
            deterministic_collation,
        )
        self.assertIn("field_id", self.get_uniques(RelationModel._meta.db_table))