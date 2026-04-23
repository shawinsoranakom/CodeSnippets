def test_html_safe(self):
        media = Media(css={"all": ["/path/to/css"]}, js=["/path/to/js"])
        self.assertTrue(hasattr(Media, "__html__"))
        self.assertEqual(str(media), media.__html__())