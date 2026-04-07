def test_unique_no_unnecessary_fk_drops(self):
        """
        If AlterField isn't selective about dropping foreign key constraints
        when modifying a field with a unique constraint, the AlterField
        incorrectly drops and recreates the Book.author foreign key even though
        it doesn't restrict the field being changed (#29193).
        """

        class Author(Model):
            name = CharField(max_length=254, unique=True)

            class Meta:
                app_label = "schema"

        class Book(Model):
            author = ForeignKey(Author, CASCADE)

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Book)
        new_field = CharField(max_length=255, unique=True)
        new_field.model = Author
        new_field.set_attributes_from_name("name")
        with self.assertLogs("django.db.backends.schema", "DEBUG") as cm:
            with connection.schema_editor() as editor:
                editor.alter_field(Author, Author._meta.get_field("name"), new_field)
        # One SQL statement is executed to alter the field.
        self.assertEqual(len(cm.records), 1)