def test_timings_captured(self):
        runner = DiscoverRunner(timing=True)
        with captured_stderr() as stderr:
            with runner.time_keeper.timed("test"):
                pass
            runner.time_keeper.print_results()
        self.assertIsInstance(runner.time_keeper, TimeKeeper)
        self.assertIn("test", stderr.getvalue())