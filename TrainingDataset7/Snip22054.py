def test_missing_file(self):
        size = images.get_image_dimensions("missing.png")
        self.assertEqual(size, (None, None))