def test_quote_name_unless_alias_deprecation(self):
        query = Query(Item)
        compiler = SQLCompiler(query, connection, None)
        msg = (
            "SQLCompiler.quote_name_unless_alias() is deprecated. "
            "Use .quote_name() instead."
        )
        with self.assertWarnsMessage(RemovedInDjango70Warning, msg) as ctx:
            self.assertEqual(
                compiler.quote_name_unless_alias("name"),
                compiler.quote_name("name"),
            )
        self.assertEqual(ctx.filename, __file__)