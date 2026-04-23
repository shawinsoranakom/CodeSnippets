def run_suite_with_runner(self, runner_class, **kwargs):
        class MyRunner(DiscoverRunner):
            def test_runner(self, *args, **kwargs):
                return runner_class()

        runner = MyRunner(**kwargs)
        # Suppress logging "Using shuffle seed" to the console.
        with captured_stdout():
            runner.setup_shuffler()
        with captured_stdout() as stdout:
            try:
                result = runner.run_suite(None)
            except RuntimeError as exc:
                result = str(exc)
        output = stdout.getvalue()
        return result, output