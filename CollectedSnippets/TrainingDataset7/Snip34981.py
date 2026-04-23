def test_timings_not_captured(self):
        runner = DiscoverRunner(timing=False)
        with captured_stderr() as stderr:
            with runner.time_keeper.timed("test"):
                pass
            runner.time_keeper.print_results()
        self.assertIsInstance(runner.time_keeper, NullTimeKeeper)
        self.assertNotIn("test", stderr.getvalue())