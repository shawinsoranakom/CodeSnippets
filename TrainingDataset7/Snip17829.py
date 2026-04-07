def test_render(self):
        widget = ReadOnlyPasswordHashWidget()
        value = (
            "pbkdf2_sha256$100000$a6Pucb1qSFcD$WmCkn9Hqidj48NVe5x0FEM6A9YiOqQcl/83m2Z5u"
            "dm0="
        )
        self.assertHTMLEqual(
            widget.render("name", value, {"id": "id_password"}),
            '<div id="id_password">'
            "  <p>"
            "    <strong>algorithm</strong>: <bdi>pbkdf2_sha256</bdi>"
            "    <strong>iterations</strong>: <bdi>100000</bdi>"
            "    <strong>salt</strong>: <bdi>a6Pucb******</bdi>"
            "    <strong>hash</strong>: "
            "       <bdi>WmCkn9**************************************</bdi>"
            "  </p>"
            '  <p><a role="button" class="button" href="../password/">'
            "Reset password</a></p>"
            "</div>",
        )