def setUp(self):
        self.orig_stdout = sys.stdout
        sys.stdout = StringIO()