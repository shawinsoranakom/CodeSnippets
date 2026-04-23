def assertTableComment(self, table, comment, using="default"):
        self.assertEqual(self._get_table_comment(table, using), comment)