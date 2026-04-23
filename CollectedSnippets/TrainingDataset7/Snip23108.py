def test_eq(self):
        self.assertEqual(MediaAsset("path/to/css"), MediaAsset("path/to/css"))
        self.assertEqual(MediaAsset("path/to/css"), "path/to/css")
        self.assertEqual(
            MediaAsset("path/to/css", media="all"), MediaAsset("path/to/css")
        )

        self.assertNotEqual(MediaAsset("path/to/css"), MediaAsset("path/to/other.css"))
        self.assertNotEqual(MediaAsset("path/to/css"), "path/to/other.css")
        self.assertNotEqual(MediaAsset("path/to/css", media="all"), CSS("path/to/css"))