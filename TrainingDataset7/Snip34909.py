def test_setupclass_exception(self):
        runner = DiscoverRunner(debug_sql=True, verbosity=0)
        suite = runner.test_suite()
        suite.addTest(self.ErrorSetUpTestDataTest())
        old_config = runner.setup_databases()
        stream = StringIO()
        runner.test_runner(
            verbosity=0,
            stream=stream,
            resultclass=runner.get_resultclass(),
        ).run(suite)
        runner.teardown_databases(old_config)
        output = stream.getvalue()
        self.assertIn(
            "ERROR: setUpClass "
            "(test_runner.test_debug_sql.TestDebugSQL.ErrorSetUpTestDataTest)",
            output,
        )