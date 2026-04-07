def test_quote_name(self):
        """'%' chars are escaped for query execution."""
        name = '"SOME%NAME"'
        quoted_name = connection.ops.quote_name(name)
        self.assertEqual(quoted_name % (), name)