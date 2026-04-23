def test_render(self):
        w = widgets.AdminURLFieldWidget()
        self.assertHTMLEqual(
            w.render("test", ""), '<input class="vURLField" name="test" type="url">'
        )
        self.assertHTMLEqual(
            w.render("test", "http://example.com"),
            '<p class="url">Currently:<a href="http://example.com">'
            "http://example.com</a><br>"
            'Change:<input class="vURLField" name="test" type="url" '
            'value="http://example.com"></p>',
        )