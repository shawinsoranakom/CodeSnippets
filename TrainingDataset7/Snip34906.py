def _test_output(self, verbosity):
        runner = DiscoverRunner(debug_sql=True, verbosity=0)
        suite = runner.test_suite()
        suite.addTest(self.FailingTest())
        suite.addTest(self.ErrorTest())
        suite.addTest(self.PassingTest())
        suite.addTest(self.PassingSubTest())
        suite.addTest(self.FailingSubTest())
        suite.addTest(self.ErrorSubTest())
        old_config = runner.setup_databases()
        stream = StringIO()
        resultclass = runner.get_resultclass()
        runner.test_runner(
            verbosity=verbosity,
            stream=stream,
            resultclass=resultclass,
        ).run(suite)
        runner.teardown_databases(old_config)

        return stream.getvalue()