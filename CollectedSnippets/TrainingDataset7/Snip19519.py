def setUp(self):
        simple_system_check.kwargs = None
        tagged_system_check.kwargs = None
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = StringIO(), StringIO()