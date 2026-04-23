def test_autofield_to_o2o(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Note)

        # Rename the field.
        old_field = Author._meta.get_field("id")
        new_field = AutoField(primary_key=True)
        new_field.set_attributes_from_name("note_ptr")
        new_field.model = Author

        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        # Alter AutoField to OneToOneField.
        new_field_o2o = OneToOneField(Note, CASCADE)
        new_field_o2o.set_attributes_from_name("note_ptr")
        new_field_o2o.model = Author

        with connection.schema_editor() as editor:
            editor.alter_field(Author, new_field, new_field_o2o, strict=True)
        columns = self.column_classes(Author)
        field_type, _ = columns["note_ptr_id"]
        self.assertEqual(
            field_type, connection.features.introspected_field_types["BigIntegerField"]
        )