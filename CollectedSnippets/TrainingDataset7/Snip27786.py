def _test_to_python(self, f):
        self.assertIs(f.to_python(1), True)
        self.assertIs(f.to_python(0), False)