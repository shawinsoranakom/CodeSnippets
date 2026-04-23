def test_url_display_for_field(self):
        model_field = models.URLField()
        display_value = display_for_field(
            "http://example.com", model_field, self.empty_value
        )
        expected = '<a href="http://example.com">http://example.com</a>'
        self.assertHTMLEqual(display_value, expected)