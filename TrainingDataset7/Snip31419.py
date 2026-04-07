def test_unique_constraint_field_and_expression(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        constraint = UniqueConstraint(
            F("height").desc(),
            "uuid",
            Lower("name").asc(),
            name="func_f_lower_field_unq",
        )
        # Add constraint.
        with connection.schema_editor() as editor:
            editor.add_constraint(Author, constraint)
            sql = constraint.create_sql(Author, editor)
        table = Author._meta.db_table
        if connection.features.supports_index_column_ordering:
            self.assertIndexOrder(table, constraint.name, ["DESC", "ASC", "ASC"])
        constraints = self.get_constraints(table)
        self.assertIs(constraints[constraint.name]["unique"], True)
        self.assertEqual(len(constraints[constraint.name]["columns"]), 3)
        self.assertEqual(constraints[constraint.name]["columns"][1], "uuid")
        # SQL contains database functions and columns.
        self.assertIs(sql.references_column(table, "height"), True)
        self.assertIs(sql.references_column(table, "name"), True)
        self.assertIs(sql.references_column(table, "uuid"), True)
        self.assertIn("LOWER(%s)" % editor.quote_name("name"), str(sql))
        # Remove constraint.
        with connection.schema_editor() as editor:
            editor.remove_constraint(Author, constraint)
        self.assertNotIn(constraint.name, self.get_constraints(table))