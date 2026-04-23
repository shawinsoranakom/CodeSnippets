def test_alter_auto_field_to_integer_field(self):
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        # Change AutoField to IntegerField
        old_field = Author._meta.get_field("id")
        new_field = IntegerField(primary_key=True)
        new_field.set_attributes_from_name("id")
        new_field.model = Author
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        # Now that ID is an IntegerField, the database raises an error if it
        # isn't provided.
        if not connection.features.supports_unspecified_pk:
            with self.assertRaises(DatabaseError):
                Author.objects.create()