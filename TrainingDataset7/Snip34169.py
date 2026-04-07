def test_reset_all_loaders(self, mock_reset):
        autoreload.reset_loaders()
        self.assertEqual(mock_reset.call_count, 2)