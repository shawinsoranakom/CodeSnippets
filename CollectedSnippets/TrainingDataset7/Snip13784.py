def run_suite(self, suite, **kwargs):
        kwargs = self.get_test_runner_kwargs()
        runner = self.test_runner(**kwargs)
        try:
            return runner.run(suite)
        finally:
            if self._shuffler is not None:
                seed_display = self._shuffler.seed_display
                self.log(f"Used shuffle seed: {seed_display}")