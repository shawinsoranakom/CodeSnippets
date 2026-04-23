def test_utf8(self):
        txt = MIMEText("UTF-8 encoded body", "plain", "utf-8")
        self.assertIn("Content-Transfer-Encoding: base64", txt.as_string())