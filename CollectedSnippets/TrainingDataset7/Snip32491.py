def test_template_tag_absolute_root(self):
        """
        Like test_template_tag_absolute, but for a file in STATIC_ROOT
        (#26249).
        """
        relpath = self.hashed_file_path("absolute_root.css")
        self.assertEqual(relpath, "absolute_root.f821df1b64f7.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertNotIn(b"/static/styles_root.css", content)
            self.assertIn(b"/static/styles_root.401f2509a628.css", content)
        self.assertPostCondition()