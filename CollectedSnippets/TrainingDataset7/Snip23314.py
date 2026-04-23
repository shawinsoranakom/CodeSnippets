def test_attrs_not_localized(self):
        self.check_html(
            self.widget,
            "name",
            "value",
            '<input type="number" name="name" value="value" max="12345" min="1234" '
            'step="9999">',
        )