def test_attrs_safestring(self):
        widget = TextInput(attrs={"onBlur": mark_safe("function('foo')")})
        self.check_html(
            widget,
            "email",
            "",
            html='<input onBlur="function(\'foo\')" type="text" name="email">',
        )