def test_was_modified_since_fp(self):
        """
        A floating point mtime does not disturb was_modified_since (#18675).
        """
        mtime = 1343416141.107817
        header = http_date(mtime)
        self.assertFalse(was_modified_since(header, mtime))