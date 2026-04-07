def assertTableCommentNotExists(self, table, using="default"):
        self.assertIn(self._get_table_comment(table, using), [None, ""])