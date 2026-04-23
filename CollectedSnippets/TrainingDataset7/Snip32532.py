def test_template_tag_simple_content(self):
        relpath = self.hashed_file_path("cached/styles.css")
        self.assertEqual(relpath, "cached/styles.deploy12345.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertNotIn(b"cached/other.css", content)
            self.assertIn(b"other.deploy12345.css", content)