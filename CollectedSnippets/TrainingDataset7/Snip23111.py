def test_repr(self):
        self.assertEqual(repr(MediaAsset("path/to/css")), "MediaAsset('path/to/css')")
        self.assertEqual(
            repr(MediaAsset("http://media.other.com/path/to/css")),
            "MediaAsset('http://media.other.com/path/to/css')",
        )