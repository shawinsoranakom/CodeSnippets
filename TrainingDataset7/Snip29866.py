def test_op_class_descending_partial_tablespace(self):
        index_name = "test_op_class_descending_partial_tablespace"
        index = Index(
            OpClass(Lower("field").desc(), name="text_pattern_ops"),
            name=index_name,
            condition=Q(field__contains="China"),
            db_tablespace="pg_default",
        )
        with connection.schema_editor() as editor:
            editor.add_index(TextFieldModel, index)
            self.assertIn(
                'TABLESPACE "pg_default" ',
                str(index.create_sql(TextFieldModel, editor)),
            )
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query, [index_name])
            self.assertCountEqual(cursor.fetchall(), [("text_pattern_ops", index_name)])
        constraints = self.get_constraints(TextFieldModel._meta.db_table)
        self.assertIn(index_name, constraints)
        self.assertEqual(constraints[index_name]["orders"], ["DESC"])