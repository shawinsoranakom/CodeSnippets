def test_rename_table_references_without_alias(self):
        compiler = Query(Person, alias_cols=False).get_compiler(connection=connection)
        table = Person._meta.db_table
        expressions = Expressions(
            table=table,
            expressions=ExpressionList(
                IndexExpression(Upper("last_name")),
                IndexExpression(F("first_name")),
            ).resolve_expression(compiler.query),
            compiler=compiler,
            quote_value=self.editor.quote_value,
        )
        expressions.rename_table_references(table, "other")
        self.assertIs(expressions.references_table(table), False)
        self.assertIs(expressions.references_table("other"), True)
        expected_str = "(UPPER(%s)), %s" % (
            self.editor.quote_name("last_name"),
            self.editor.quote_name("first_name"),
        )
        self.assertEqual(str(expressions), expected_str)