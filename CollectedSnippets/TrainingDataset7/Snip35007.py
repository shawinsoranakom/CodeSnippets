def pickle_error_test(self):
        with self.subTest("TypeError: cannot pickle memoryview object"):
            self.x = memoryview(b"")
            self.fail("expected failure")