def test_hashed_name(self):
        relpath = self.hashed_file_path("cached/styles.css")
        self.assertEqual(relpath, "cached/styles.css")