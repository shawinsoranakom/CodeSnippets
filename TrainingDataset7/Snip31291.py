def test_no_db_constraint_added_during_primary_key_change(self):
        """
        When a primary key that's pointed to by a ForeignKey with
        db_constraint=False is altered, a foreign key constraint isn't added.
        """

        class Author(Model):
            class Meta:
                app_label = "schema"

        class BookWeak(Model):
            author = ForeignKey(Author, CASCADE, db_constraint=False)

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(BookWeak)
        self.assertForeignKeyNotExists(BookWeak, "author_id", "schema_author")
        old_field = Author._meta.get_field("id")
        new_field = BigAutoField(primary_key=True)
        new_field.model = Author
        new_field.set_attributes_from_name("id")
        # @isolate_apps() and inner models are needed to have the model
        # relations populated, otherwise this doesn't act as a regression test.
        self.assertEqual(len(new_field.model._meta.related_objects), 1)
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        self.assertForeignKeyNotExists(BookWeak, "author_id", "schema_author")