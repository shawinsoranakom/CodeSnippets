def test_7bit(self):
        txt = MIMEText("Body with only ASCII characters.", "plain", "utf-8")
        self.assertIn("Content-Transfer-Encoding: base64", txt.as_string())