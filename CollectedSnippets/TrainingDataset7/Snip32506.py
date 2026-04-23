def test_js_source_map_sensitive(self):
        relpath = self.hashed_file_path("cached/source_map_sensitive.js")
        self.assertEqual(relpath, "cached/source_map_sensitive.5da96fdd3cb3.js")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertIn(b"//# sOuRcEMaPpInGURL=source_map.js.map", content)
            self.assertNotIn(
                b"//# sourceMappingURL=source_map.js.99914b932bd3.map",
                content,
            )
        self.assertPostCondition()