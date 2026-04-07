def test_label_attrs_not_localized(self):
        form = Person()
        field = form["first_name"]
        self.assertHTMLEqual(
            field.label_tag(attrs={"number": 9999}),
            '<label number="9999" for="id_first_name">First name:</label>',
        )
        self.assertHTMLEqual(
            field.legend_tag(attrs={"number": 9999}),
            '<legend number="9999">First name:</legend>',
        )