def test_setup_shuffler_no_shuffle_argument(self):
        runner = DiscoverRunner()
        self.assertIs(runner.shuffle, False)
        runner.setup_shuffler()
        self.assertIsNone(runner.shuffle_seed)