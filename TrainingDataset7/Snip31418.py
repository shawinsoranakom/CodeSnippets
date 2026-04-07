def test_composite_func_unique_constraint(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(BookWithSlug)
        constraint = UniqueConstraint(
            Upper("title"),
            Lower("slug"),
            name="func_upper_lower_unq",
        )
        # Add constraint.
        with connection.schema_editor() as editor:
            editor.add_constraint(BookWithSlug, constraint)
            sql = constraint.create_sql(BookWithSlug, editor)
        table = BookWithSlug._meta.db_table
        constraints = self.get_constraints(table)
        self.assertIn(constraint.name, constraints)
        self.assertIs(constraints[constraint.name]["unique"], True)
        # SQL contains database functions.
        self.assertIs(sql.references_column(table, "title"), True)
        self.assertIs(sql.references_column(table, "slug"), True)
        sql = str(sql)
        self.assertIn("UPPER(%s)" % editor.quote_name("title"), sql)
        self.assertIn("LOWER(%s)" % editor.quote_name("slug"), sql)
        self.assertLess(sql.index("UPPER"), sql.index("LOWER"))
        # Remove constraint.
        with connection.schema_editor() as editor:
            editor.remove_constraint(BookWithSlug, constraint)
        self.assertNotIn(constraint.name, self.get_constraints(table))