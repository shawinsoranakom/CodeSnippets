def test_modules(self):
        output = self.engine.render_to_string("modules", {})
        self.assertIn(
            "&#x27;django&#x27;: &lt;module &#x27;django&#x27; ",
            output,
        )