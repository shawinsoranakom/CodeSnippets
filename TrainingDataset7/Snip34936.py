def test_setup_shuffler_shuffle_none(self):
        runner = DiscoverRunner(shuffle=None)
        self.assertIsNone(runner.shuffle)
        with mock.patch("random.randint", return_value=1):
            with captured_stdout() as stdout:
                runner.setup_shuffler()
        self.assertEqual(stdout.getvalue(), "Using shuffle seed: 1 (generated)\n")
        self.assertEqual(runner.shuffle_seed, 1)