def test_hash(self):
        self.assertEqual(hash(MediaAsset("path/to/css")), hash("path/to/css"))
        self.assertEqual(
            hash(MediaAsset("path/to/css")), hash(MediaAsset("path/to/css"))
        )