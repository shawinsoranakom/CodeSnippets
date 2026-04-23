def test_boundfield_css_classes(self):
        form = Person()
        field = form["first_name"]
        self.assertEqual(field.css_classes(), "")
        self.assertEqual(field.css_classes(extra_classes=""), "")
        self.assertEqual(field.css_classes(extra_classes="test"), "test")
        self.assertEqual(field.css_classes(extra_classes="test test"), "test")