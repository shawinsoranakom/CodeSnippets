def test_alter_primary_key_the_same_name(self):
        with connection.schema_editor() as editor:
            editor.create_model(Thing)

        old_field = Thing._meta.get_field("when")
        new_field = CharField(max_length=2, primary_key=True)
        new_field.set_attributes_from_name("when")
        new_field.model = Thing
        with connection.schema_editor() as editor:
            editor.alter_field(Thing, old_field, new_field, strict=True)
        self.assertEqual(self.get_primary_key(Thing._meta.db_table), "when")
        with connection.schema_editor() as editor:
            editor.alter_field(Thing, new_field, old_field, strict=True)
        self.assertEqual(self.get_primary_key(Thing._meta.db_table), "when")