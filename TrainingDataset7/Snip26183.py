def test_8bit_non_latin(self):
        txt = MIMEText(
            "Body with non latin characters: А Б В Г Д Е Ж Ѕ З И І К Л М Н О П.",
            "plain",
            "utf-8",
        )
        self.assertIn("Content-Transfer-Encoding: base64", txt.as_string())