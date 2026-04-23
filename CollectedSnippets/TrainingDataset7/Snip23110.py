def test_str(self):
        self.assertEqual(
            str(MediaAsset("path/to/css")),
            "http://media.example.com/static/path/to/css",
        )
        self.assertEqual(
            str(MediaAsset("http://media.other.com/path/to/css")),
            "http://media.other.com/path/to/css",
        )