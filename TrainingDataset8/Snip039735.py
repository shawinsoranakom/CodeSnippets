def test_get_extension_for_mimetype(self, mimetype: str, expected_extension: str):
        result = get_extension_for_mimetype(mimetype)
        self.assertEqual(expected_extension, result)