def tearDown(self):
        sys.stdout.close()  # sys.stdout is a StringIO at this point.
        sys.stdout = self.orig_stdout