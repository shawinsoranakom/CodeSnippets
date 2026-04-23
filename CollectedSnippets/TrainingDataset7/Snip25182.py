def test_alter_field_unique_false_removes_deferred_sql(self):
        field_added = CharField(max_length=127, unique=True)
        field_added.set_attributes_from_name("charfield_added")

        field_to_alter = CharField(max_length=127, unique=True)
        field_to_alter.set_attributes_from_name("charfield_altered")
        altered_field = CharField(max_length=127, unique=False)
        altered_field.set_attributes_from_name("charfield_altered")

        with connection.schema_editor() as editor:
            editor.add_field(ArticleTranslation, field_added)
            editor.add_field(ArticleTranslation, field_to_alter)
            self.assertEqual(len(editor.deferred_sql), 2)
            editor.alter_field(ArticleTranslation, field_to_alter, altered_field)
            self.assertEqual(len(editor.deferred_sql), 1)
            self.assertIn("charfield_added", str(editor.deferred_sql[0].parts["name"]))