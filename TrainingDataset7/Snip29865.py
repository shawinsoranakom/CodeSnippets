def test_op_class_descending_partial(self):
        index_name = "test_op_class_descending_partial"
        index = Index(
            OpClass(Lower("field"), name="text_pattern_ops").desc(),
            name=index_name,
            condition=Q(field__contains="China"),
        )
        with connection.schema_editor() as editor:
            editor.add_index(TextFieldModel, index)
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query, [index_name])
            self.assertCountEqual(cursor.fetchall(), [("text_pattern_ops", index_name)])
        constraints = self.get_constraints(TextFieldModel._meta.db_table)
        self.assertIn(index_name, constraints)
        self.assertEqual(constraints[index_name]["orders"], ["DESC"])