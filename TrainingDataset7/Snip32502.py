def test_css_source_map_sensitive(self):
        relpath = self.hashed_file_path("cached/source_map_sensitive.css")
        self.assertEqual(relpath, "cached/source_map_sensitive.456683f2106f.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertIn(b"/*# sOuRcEMaPpInGURL=source_map.css.map */", content)
            self.assertNotIn(
                b"/*# sourceMappingURL=source_map.css.99914b932bd3.map */",
                content,
            )
        self.assertPostCondition()