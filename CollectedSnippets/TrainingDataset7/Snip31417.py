def test_func_unique_constraint(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        constraint = UniqueConstraint(Upper("name").desc(), name="func_upper_uq")
        # Add constraint.
        with connection.schema_editor() as editor:
            editor.add_constraint(Author, constraint)
            sql = constraint.create_sql(Author, editor)
        table = Author._meta.db_table
        constraints = self.get_constraints(table)
        if connection.features.supports_index_column_ordering:
            self.assertIndexOrder(table, constraint.name, ["DESC"])
        self.assertIn(constraint.name, constraints)
        self.assertIs(constraints[constraint.name]["unique"], True)
        # SQL contains a database function.
        self.assertIs(sql.references_column(table, "name"), True)
        self.assertIn("UPPER(%s)" % editor.quote_name("name"), str(sql))
        # Remove constraint.
        with connection.schema_editor() as editor:
            editor.remove_constraint(Author, constraint)
        self.assertNotIn(constraint.name, self.get_constraints(table))