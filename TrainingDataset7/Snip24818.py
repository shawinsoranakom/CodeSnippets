def test_text_charset(self):
        for content_type, content in [
            (None, b"Ol\xc3\xa1 Mundo"),
            ("text/plain; charset=utf-8", b"Ol\xc3\xa1 Mundo"),
            ("text/plain; charset=iso-8859-1", b"Ol\xe1 Mundo"),
        ]:
            with self.subTest(content_type=content_type):
                response = HttpResponse(content, content_type=content_type)
                self.assertEqual(response.text, "Olá Mundo")