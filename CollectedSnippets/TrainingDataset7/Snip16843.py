def test_render_idn(self):
        w = widgets.AdminURLFieldWidget()
        self.assertHTMLEqual(
            w.render("test", "http://example-äüö.com"),
            '<p class="url">Currently: <a href="http://example-%C3%A4%C3%BC%C3%B6.com">'
            "http://example-äüö.com</a><br>"
            'Change:<input class="vURLField" name="test" type="url" '
            'value="http://example-äüö.com"></p>',
        )
        # Does not use obsolete IDNA-2003 encoding (#36013).
        self.assertNotIn("fass.example.com", w.render("test", "http://faß.example.com"))