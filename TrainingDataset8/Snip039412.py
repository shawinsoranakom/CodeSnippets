def test_no_stats(self):
        self.assertEqual([], get_memo_stats_provider().get_stats())