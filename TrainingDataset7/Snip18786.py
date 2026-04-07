def setUp(self):
        compiler = Person.objects.all().query.get_compiler(connection.alias)
        self.editor = connection.schema_editor()
        self.expressions = Expressions(
            table=Person._meta.db_table,
            expressions=ExpressionList(
                IndexExpression(F("first_name")),
                IndexExpression(F("last_name").desc()),
                IndexExpression(Upper("last_name")),
            ).resolve_expression(compiler.query),
            compiler=compiler,
            quote_value=self.editor.quote_value,
        )