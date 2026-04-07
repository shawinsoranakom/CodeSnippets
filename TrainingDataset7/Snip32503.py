def test_css_source_map_data_uri(self):
        relpath = self.hashed_file_path("cached/source_map_data_uri.css")
        self.assertEqual(relpath, "cached/source_map_data_uri.3166be10260d.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            source_map_data_uri = (
                b"/*# sourceMappingURL=data:application/json;charset=utf8;base64,"
                b"eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIl9zcmMv*/"
            )
            self.assertIn(source_map_data_uri, content)
        self.assertPostCondition()