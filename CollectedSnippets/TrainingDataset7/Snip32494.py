def test_template_tag_deep_relative(self):
        relpath = self.hashed_file_path("cached/css/window.css")
        self.assertEqual(relpath, "cached/css/window.5d5c10836967.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertNotIn(b"url(img/window.png)", content)
            self.assertIn(b'url("img/window.acae32e4532b.png")', content)
        self.assertPostCondition()