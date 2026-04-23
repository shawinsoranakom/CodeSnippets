def test_add_db_comment_charfield(self):
        comment = "Custom comment"
        field = CharField(max_length=255, db_comment=comment)
        field.set_attributes_from_name("name_with_comment")
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.add_field(Author, field)
        self.assertEqual(
            self.get_column_comment(Author._meta.db_table, "name_with_comment"),
            comment,
        )