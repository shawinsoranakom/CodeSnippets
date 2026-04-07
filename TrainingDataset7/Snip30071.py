def test_as_sql(self):
        query = Line.objects.all().query
        compiler = query.get_compiler(connection.alias)

        tests = (
            (Lexeme("a"), ("'a'",)),
            (Lexeme("a", invert=True), ("!'a'",)),
            (~Lexeme("a"), ("!'a'",)),
            (Lexeme("a", prefix=True), ("'a':*",)),
            (Lexeme("a", weight="D"), ("'a':D",)),
            (Lexeme("a", invert=True, prefix=True, weight="D"), ("!'a':*D",)),
            (Lexeme("a") | Lexeme("b") & ~Lexeme("c"), ("('a' | ('b' & !'c'))",)),
            (
                ~(Lexeme("a") | Lexeme("b") & ~Lexeme("c")),
                ("(!'a' & (!'b' | 'c'))",),
            ),
        )

        for expression, expected_params in tests:
            with self.subTest(expression=expression, expected_params=expected_params):
                _, params = expression.as_sql(compiler, connection)
                self.assertEqual(params, expected_params)