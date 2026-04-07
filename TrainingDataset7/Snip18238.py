def test_valid_password(self):
        value = (
            "pbkdf2_sha256$100000$a6Pucb1qSFcD$WmCkn9Hqidj48NVe5x0FEM6A9YiOqQcl/83m2Z5u"
            "dm0="
        )
        hashed_html = (
            "<p><strong>algorithm</strong>: <bdi>pbkdf2_sha256</bdi> "
            "<strong>iterations</strong>: <bdi>100000</bdi> "
            "<strong>salt</strong>: <bdi>a6Pucb******</bdi> "
            "<strong>hash</strong>: <bdi>WmCkn9**************************************"
            "</bdi></p>"
        )
        self.assertEqual(render_password_as_hash(value), hashed_html)