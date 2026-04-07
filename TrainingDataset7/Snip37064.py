def test_was_modified_since_empty_string(self):
        self.assertTrue(was_modified_since(header="", mtime=1))