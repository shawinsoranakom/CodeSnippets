def test_alter_text_field_to_not_null_with_default_value(self):
        with connection.schema_editor() as editor:
            editor.create_model(Note)
        note = Note.objects.create(address=None)
        old_field = Note._meta.get_field("address")
        new_field = TextField(blank=True, default="", null=False)
        new_field.set_attributes_from_name("address")
        with connection.schema_editor() as editor:
            editor.alter_field(Note, old_field, new_field, strict=True)
        note.refresh_from_db()
        self.assertEqual(note.address, "")