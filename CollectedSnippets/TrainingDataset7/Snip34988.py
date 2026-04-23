def get_databases(self, test_labels):
        with captured_stdout() as stdout:
            suite = self.runner.build_suite(test_labels)
            databases = self.runner.get_databases(suite)
        return databases, stdout.getvalue()