def test_stylesheet_attribute_escaping(self):
        style = feedgenerator.Stylesheet(
            url='http://example.com/style.css?foo="bar"&baz=<>',
            mimetype='text/css; charset="utf-8"',
            media='screen and (max-width: "600px")',
        )

        self.assertEqual(
            str(style),
            'href="http://example.com/style.css?foo=%22bar%22&amp;baz=%3C%3E" '
            'media="screen and (max-width: &quot;600px&quot;)" '
            'type="text/css; charset=&quot;utf-8&quot;"',
        )