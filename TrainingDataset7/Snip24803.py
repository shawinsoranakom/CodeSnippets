def test_non_string_content(self):
        # Bug 16494: HttpResponse should behave consistently with non-strings
        r = HttpResponse(12345)
        self.assertEqual(r.content, b"12345")

        # test content via property
        r = HttpResponse()
        r.content = 12345
        self.assertEqual(r.content, b"12345")