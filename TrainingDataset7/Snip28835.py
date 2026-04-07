def test_tablespace_ignored_for_indexed_field(self):
        # No tablespace-related SQL
        self.assertEqual(sql_for_table(Article), sql_for_table(ArticleRef))