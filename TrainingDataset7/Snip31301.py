def test_add_field_o2o_nullable(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Note)
        new_field = OneToOneField(Note, CASCADE, null=True)
        new_field.set_attributes_from_name("note")
        with connection.schema_editor() as editor:
            editor.add_field(Author, new_field)
        columns = self.column_classes(Author)
        self.assertIn("note_id", columns)
        self.assertTrue(columns["note_id"][1][6])