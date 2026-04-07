def test_path(self):
        asset = MediaAsset("path/to/css")
        self.assertEqual(asset.path, "http://media.example.com/static/path/to/css")

        asset = MediaAsset("http://media.other.com/path/to/css")
        self.assertEqual(asset.path, "http://media.other.com/path/to/css")

        asset = MediaAsset("https://secure.other.com/path/to/css")
        self.assertEqual(asset.path, "https://secure.other.com/path/to/css")

        asset = MediaAsset("/absolute/path/to/css")
        self.assertEqual(asset.path, "/absolute/path/to/css")

        asset = MediaAsset("//absolute/path/to/css")
        self.assertEqual(asset.path, "//absolute/path/to/css")