def test_m2m_rename(self):
        class LocalBook(Model):
            authors = ManyToManyField("schema.Author")

            class Meta:
                app_label = "schema"
                apps = new_apps

        self.local_models = [LocalBook]
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(LocalBook)
        old_field = LocalBook._meta.get_field("authors")
        new_field = ManyToManyField("schema.Author")
        new_field.contribute_to_class(LocalBook, "writers")
        with connection.schema_editor() as editor:
            editor.alter_field(LocalBook, old_field, new_field, strict=True)
        # Ensure old M2M is gone.
        with self.assertRaises(DatabaseError):
            self.column_classes(
                LocalBook._meta.get_field("authors").remote_field.through
            )
        if connection.features.supports_foreign_keys:
            self.assertForeignKeyExists(
                new_field.remote_field.through,
                "author_id",
                "schema_author",
            )
        new_through_table = new_field.remote_field.through._meta.db_table
        self.assertIn("writers", new_through_table)
        self.assertNotIn("authors", new_through_table)
        # Remove the old field from meta for tearDown().
        LocalBook._meta.local_many_to_many.remove(old_field)