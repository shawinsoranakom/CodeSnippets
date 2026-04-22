def test_image_may_have_alpha_channel(self, format: str, expected_alpha: bool):
        img = Image.new(format, (1, 1))
        self.assertEqual(image._image_may_have_alpha_channel(img), expected_alpha)