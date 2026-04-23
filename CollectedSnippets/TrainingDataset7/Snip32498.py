def test_css_import_case_insensitive(self):
        relpath = self.hashed_file_path("cached/styles_insensitive.css")
        self.assertEqual(relpath, "cached/styles_insensitive.3fa427592a53.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertNotIn(b"cached/other.css", content)
            self.assertIn(b"other.d41d8cd98f00.css", content)
        self.assertPostCondition()