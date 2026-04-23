def test_fk(self):
        "Creating tables out of FK order, then repointing, works"
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Book)
            editor.create_model(Author)
            editor.create_model(Tag)
        # Initial tables are there
        list(Author.objects.all())
        list(Book.objects.all())
        # Make sure the FK constraint is present
        with self.assertRaises(IntegrityError):
            Book.objects.create(
                author_id=1,
                title="Much Ado About Foreign Keys",
                pub_date=datetime.datetime.now(),
            )
        # Repoint the FK constraint
        old_field = Book._meta.get_field("author")
        new_field = ForeignKey(Tag, CASCADE)
        new_field.set_attributes_from_name("author")
        with connection.schema_editor() as editor:
            editor.alter_field(Book, old_field, new_field, strict=True)
        self.assertForeignKeyExists(Book, "author_id", "schema_tag")