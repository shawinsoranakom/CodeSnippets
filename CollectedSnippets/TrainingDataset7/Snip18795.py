def test_truncate_name(self):
        self.assertEqual(truncate_name("some_table", 10), "some_table")
        self.assertEqual(truncate_name("some_long_table", 10), "some_la38a")
        self.assertEqual(truncate_name("some_long_table", 10, 3), "some_loa38")
        self.assertEqual(truncate_name("some_long_table"), "some_long_table")
        # "user"."table" syntax
        self.assertEqual(
            truncate_name('username"."some_table', 10), 'username"."some_table'
        )
        self.assertEqual(
            truncate_name('username"."some_long_table', 10), 'username"."some_la38a'
        )
        self.assertEqual(
            truncate_name('username"."some_long_table', 10, 3), 'username"."some_loa38'
        )