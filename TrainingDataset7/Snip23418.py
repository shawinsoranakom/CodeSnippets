def test_attrs_precedence(self):
        """
        `attrs` passed to render() get precedence over those passed to the
        constructor
        """
        widget = TextInput(attrs={"class": "pretty"})
        self.check_html(
            widget,
            "email",
            "",
            attrs={"class": "special"},
            html='<input type="text" class="special" name="email">',
        )