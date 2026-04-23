def test_unicode_file_name(self):
        f = File(None, "djángö")
        self.assertIs(type(repr(f)), str)