def test_get_primary_key_columns(self):
        self.assertEqual(
            self.get_primary_key_columns(User._meta.db_table),
            ["tenant_id", "id"],
        )
        self.assertEqual(
            self.get_primary_key_columns(Comment._meta.db_table),
            ["tenant_id", "comment_id"],
        )