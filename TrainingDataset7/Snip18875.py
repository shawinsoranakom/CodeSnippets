def _run_autocomplete(self):
        util = ManagementUtility(argv=sys.argv)
        with captured_stdout() as stdout:
            try:
                util.autocomplete()
            except SystemExit:
                pass
        return stdout.getvalue().strip().split("\n")