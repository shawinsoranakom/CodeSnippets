def test_add_db_comment_generated_field(self):
        comment = "Custom comment"
        field = GeneratedField(
            expression=Value(1),
            db_persist=True,
            output_field=IntegerField(),
            db_comment=comment,
        )
        field.set_attributes_from_name("volume")
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.add_field(Author, field)
        self.assertEqual(
            self.get_column_comment(Author._meta.db_table, "volume"),
            comment,
        )