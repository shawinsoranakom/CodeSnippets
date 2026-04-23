def test_op_class_descending_collation(self):
        collation = connection.features.test_collations.get("non_default")
        if not collation:
            self.skipTest("This backend does not support case-insensitive collations.")
        index_name = "test_op_class_descending_collation"
        index = Index(
            Collate(
                OpClass(Lower("field"), name="text_pattern_ops").desc(nulls_last=True),
                collation=collation,
            ),
            name=index_name,
        )
        with connection.schema_editor() as editor:
            editor.add_index(TextFieldModel, index)
            self.assertIn(
                "COLLATE %s" % editor.quote_name(collation),
                str(index.create_sql(TextFieldModel, editor)),
            )
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query, [index_name])
            self.assertCountEqual(cursor.fetchall(), [("text_pattern_ops", index_name)])
        table = TextFieldModel._meta.db_table
        constraints = self.get_constraints(table)
        self.assertIn(index_name, constraints)
        self.assertEqual(constraints[index_name]["orders"], ["DESC"])
        with connection.schema_editor() as editor:
            editor.remove_index(TextFieldModel, index)
        self.assertNotIn(index_name, self.get_constraints(table))