def test_alter_null_to_not_null(self):
        """
        #23609 - Tests handling of default values when altering from NULL to
        NOT NULL.
        """
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        # Ensure the field is right to begin with
        columns = self.column_classes(Author)
        self.assertTrue(columns["height"][1][6])
        # Create some test data
        Author.objects.create(name="Not null author", height=12)
        Author.objects.create(name="Null author")
        # Verify null value
        self.assertEqual(Author.objects.get(name="Not null author").height, 12)
        self.assertIsNone(Author.objects.get(name="Null author").height)
        # Alter the height field to NOT NULL with default
        old_field = Author._meta.get_field("height")
        new_field = PositiveIntegerField(default=42)
        new_field.set_attributes_from_name("height")
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        columns = self.column_classes(Author)
        self.assertFalse(columns["height"][1][6])
        # Verify default value
        self.assertEqual(Author.objects.get(name="Not null author").height, 12)
        self.assertEqual(Author.objects.get(name="Null author").height, 42)