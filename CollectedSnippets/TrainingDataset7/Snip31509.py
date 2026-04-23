def test_alter_primary_key_db_collation(self):
        collation = connection.features.test_collations.get("non_default")
        if not collation:
            self.skipTest("Language collations are not supported.")

        with connection.schema_editor() as editor:
            editor.create_model(Thing)

        old_field = Thing._meta.get_field("when")
        new_field = CharField(max_length=1, db_collation=collation, primary_key=True)
        new_field.set_attributes_from_name("when")
        new_field.model = Thing
        with connection.schema_editor() as editor:
            editor.alter_field(Thing, old_field, new_field, strict=True)
        self.assertEqual(self.get_primary_key(Thing._meta.db_table), "when")
        self.assertEqual(
            self.get_column_collation(Thing._meta.db_table, "when"),
            collation,
        )
        with connection.schema_editor() as editor:
            editor.alter_field(Thing, new_field, old_field, strict=True)
        self.assertEqual(self.get_primary_key(Thing._meta.db_table), "when")
        self.assertIsNone(self.get_column_collation(Thing._meta.db_table, "when"))