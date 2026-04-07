def test_setup_shuffler_shuffle_int(self):
        runner = DiscoverRunner(shuffle=2)
        self.assertEqual(runner.shuffle, 2)
        with captured_stdout() as stdout:
            runner.setup_shuffler()
        expected_out = "Using shuffle seed: 2 (given)\n"
        self.assertEqual(stdout.getvalue(), expected_out)
        self.assertEqual(runner.shuffle_seed, 2)