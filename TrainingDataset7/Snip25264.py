def test_table_names(self):
        tl = connection.introspection.table_names()
        self.assertEqual(tl, sorted(tl))
        self.assertIn(
            Reporter._meta.db_table,
            tl,
            "'%s' isn't in table_list()." % Reporter._meta.db_table,
        )
        self.assertIn(
            Article._meta.db_table,
            tl,
            "'%s' isn't in table_list()." % Article._meta.db_table,
        )