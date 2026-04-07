def test_init(self):
        attributes = {"media": "all", "is": "magic-css"}
        asset = MediaAsset("path/to/css", **attributes)
        self.assertEqual(asset._path, "path/to/css")
        self.assertEqual(asset.attributes, attributes)
        self.assertIsNot(asset.attributes, attributes)