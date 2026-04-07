def test_css_source_map_tabs(self):
        relpath = self.hashed_file_path("cached/source_map_tabs.css")
        self.assertEqual(relpath, "cached/source_map_tabs.b2fceaf426aa.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertNotIn(b"/*#\tsourceMappingURL=source_map.css.map\t*/", content)
            self.assertIn(
                b"/*# sourceMappingURL=source_map.css.99914b932bd3.map */",
                content,
            )
        self.assertPostCondition()