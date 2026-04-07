def test_parent_path(self):
        with self.assertRaises(SuspiciousFileOperation):
            safe_join("/abc/", "../def")