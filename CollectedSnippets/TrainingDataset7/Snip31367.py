def test_db_default_equivalent_sql_noop(self):
        class Author(Model):
            name = TextField(db_default=Value("foo"))

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(Author)

        new_field = TextField(db_default="foo")
        new_field.set_attributes_from_name("name")
        new_field.model = Author
        with connection.schema_editor() as editor, self.assertNumQueries(0):
            editor.alter_field(Author, Author._meta.get_field("name"), new_field)