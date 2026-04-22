def test_image_to_url_prefix(self, img, expected_prefix):
        url = image.image_to_url(
            img,
            width=-1,
            clamp=False,
            channels="RGB",
            output_format="JPEG",
            image_id="blah",
        )
        self.assertTrue(url.startswith(expected_prefix))