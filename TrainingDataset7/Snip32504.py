def test_js_source_map(self):
        relpath = self.hashed_file_path("cached/source_map.js")
        self.assertEqual(relpath, "cached/source_map.cd45b8534a87.js")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertNotIn(b"//# sourceMappingURL=source_map.js.map", content)
            self.assertIn(
                b"//# sourceMappingURL=source_map.js.99914b932bd3.map",
                content,
            )
        self.assertPostCondition()