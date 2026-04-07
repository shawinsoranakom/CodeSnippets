def test_render_invalid_password_format(self):
        widget = ReadOnlyPasswordHashWidget()
        value = "pbkdf2_sh"
        self.assertHTMLEqual(
            widget.render("name", value, {}),
            "<div><p>"
            "<strong>Invalid password format or unknown hashing algorithm.</strong>"
            '</p><p><a role="button" class="button" href="../password/">Reset password'
            "</a></p></div>",
        )