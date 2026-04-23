def test_op_class(self):
        index_name = "test_op_class"
        index = Index(
            OpClass(Lower("field"), name="text_pattern_ops"),
            name=index_name,
        )
        with connection.schema_editor() as editor:
            editor.add_index(TextFieldModel, index)
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query, [index_name])
            self.assertCountEqual(cursor.fetchall(), [("text_pattern_ops", index_name)])