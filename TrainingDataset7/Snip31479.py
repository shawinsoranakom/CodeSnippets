def test_add_db_comment_and_default_charfield(self):
        comment = "Custom comment with default"
        field = CharField(max_length=255, default="Joe Doe", db_comment=comment)
        field.set_attributes_from_name("name_with_comment_default")
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            Author.objects.create(name="Before adding a new field")
            editor.add_field(Author, field)

        self.assertEqual(
            self.get_column_comment(Author._meta.db_table, "name_with_comment_default"),
            comment,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT name_with_comment_default FROM {Author._meta.db_table};"
            )
            for row in cursor.fetchall():
                self.assertEqual(row[0], "Joe Doe")