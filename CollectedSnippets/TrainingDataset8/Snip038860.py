def test_image_to_url_suffix(self, img, expected_suffix):
        url = image.image_to_url(
            img,
            width=-1,
            clamp=False,
            channels="RGB",
            output_format="auto",
            image_id="blah",
        )
        self.assertTrue(url.endswith(expected_suffix))