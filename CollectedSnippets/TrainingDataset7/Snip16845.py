def test_attrs(self):
        w = widgets.AdminUUIDInputWidget()
        self.assertHTMLEqual(
            w.render("test", "550e8400-e29b-41d4-a716-446655440000"),
            '<input value="550e8400-e29b-41d4-a716-446655440000" type="text" '
            'class="vUUIDField" name="test">',
        )
        w = widgets.AdminUUIDInputWidget(attrs={"class": "myUUIDInput"})
        self.assertHTMLEqual(
            w.render("test", "550e8400-e29b-41d4-a716-446655440000"),
            '<input value="550e8400-e29b-41d4-a716-446655440000" type="text" '
            'class="myUUIDInput" name="test">',
        )