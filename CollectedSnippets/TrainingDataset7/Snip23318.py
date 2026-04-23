def test_render_value_true(self):
        """
        The render_value argument lets you specify whether the widget should
        render its value. For security reasons, this is off by default.
        """
        widget = PasswordInput(render_value=True)
        self.check_html(
            widget, "password", "", html='<input type="password" name="password">'
        )
        self.check_html(
            widget, "password", None, html='<input type="password" name="password">'
        )
        self.check_html(
            widget,
            "password",
            "test@example.com",
            html='<input type="password" name="password" value="test@example.com">',
        )