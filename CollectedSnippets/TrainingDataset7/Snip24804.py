def test_memoryview_content(self):
        r = HttpResponse(memoryview(b"memoryview"))
        self.assertEqual(r.content, b"memoryview")