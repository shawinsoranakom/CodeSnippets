def test_path_with_querystring(self):
        relpath = self.hashed_file_path("cached/styles.css?spam=eggs")
        self.assertEqual(relpath, "cached/styles.5e0040571e1a.css?spam=eggs")
        with storage.staticfiles_storage.open(
            "cached/styles.5e0040571e1a.css"
        ) as relfile:
            content = relfile.read()
            self.assertNotIn(b"cached/other.css", content)
            self.assertIn(b"other.d41d8cd98f00.css", content)
        self.assertPostCondition()