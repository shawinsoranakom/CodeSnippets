def test_template_tag_relative(self):
        relpath = self.hashed_file_path("cached/relative.css")
        self.assertEqual(relpath, "cached/relative.c3e9e1ea6f2e.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertNotIn(b"../cached/styles.css", content)
            self.assertNotIn(b'@import "styles.css"', content)
            self.assertNotIn(b"url(img/relative.png)", content)
            self.assertIn(b'url("img/relative.acae32e4532b.png")', content)
            self.assertIn(b"../cached/styles.5e0040571e1a.css", content)
        self.assertPostCondition()