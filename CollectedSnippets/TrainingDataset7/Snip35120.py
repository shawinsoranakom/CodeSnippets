def run_suite(self, suite, **kwargs):
                kwargs = self.get_test_runner_kwargs()
                runner = self.test_runner(**kwargs)
                return runner.run(suite)