def test_exists(self):
        with CaptureQueriesContext(connection) as captured_queries:
            self.assertFalse(Tag.objects.exists())
        # Ok - so the exist query worked - but did it include too many columns?
        self.assertEqual(len(captured_queries), 1)
        qstr = captured_queries[0]["sql"]
        id, name = connection.ops.quote_name("id"), connection.ops.quote_name("name")
        self.assertNotIn(id, qstr)
        self.assertNotIn(name, qstr)