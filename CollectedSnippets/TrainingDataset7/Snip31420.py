def test_func_unique_constraint_partial(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        constraint = UniqueConstraint(
            Upper("name"),
            name="func_upper_cond_weight_uq",
            condition=Q(weight__isnull=False),
        )
        # Add constraint.
        with connection.schema_editor() as editor:
            editor.add_constraint(Author, constraint)
            sql = constraint.create_sql(Author, editor)
        table = Author._meta.db_table
        constraints = self.get_constraints(table)
        self.assertIn(constraint.name, constraints)
        self.assertIs(constraints[constraint.name]["unique"], True)
        self.assertIs(sql.references_column(table, "name"), True)
        self.assertIn("UPPER(%s)" % editor.quote_name("name"), str(sql))
        self.assertIn(
            "WHERE %s IS NOT NULL" % editor.quote_name("weight"),
            str(sql),
        )
        # Remove constraint.
        with connection.schema_editor() as editor:
            editor.remove_constraint(Author, constraint)
        self.assertNotIn(constraint.name, self.get_constraints(table))