def test_render_no_password(self):
        widget = ReadOnlyPasswordHashWidget()
        self.assertHTMLEqual(
            widget.render("name", None, {}),
            "<div><p><strong>No password set.</p><p>"
            '<a role="button" class="button" href="../password/">Set password</a>'
            "</p></div>",
        )