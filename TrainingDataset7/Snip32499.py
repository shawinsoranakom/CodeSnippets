def test_css_data_uri_with_nested_url(self):
        relpath = self.hashed_file_path("cached/data_uri_with_nested_url.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertIn(b'url("data:image/svg+xml,url(%23b) url(%23c)")', content)
        self.assertPostCondition()