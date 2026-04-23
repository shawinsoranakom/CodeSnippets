def test_no_stats(self):
        self.assertEqual([], get_singleton_stats_provider().get_stats())