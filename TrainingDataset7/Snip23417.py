def test_constructor_attrs(self):
        widget = TextInput(attrs={"class": "fun", "type": "email"})
        self.check_html(
            widget, "email", "", html='<input type="email" class="fun" name="email">'
        )
        self.check_html(
            widget,
            "email",
            "foo@example.com",
            html=(
                '<input type="email" class="fun" value="foo@example.com" name="email">'
            ),
        )