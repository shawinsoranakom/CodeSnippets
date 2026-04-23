def test_alter_db_table_no_changes(self):
        """
        Alter_db_table doesn't generate a migration if no changes have been
        made.
        """
        changes = self.get_changes(
            [self.author_with_db_table_options], [self.author_with_db_table_options]
        )
        # Right number of migrations?
        self.assertEqual(len(changes), 0)