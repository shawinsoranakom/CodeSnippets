def test_lazy_content(self):
        r = HttpResponse(lazystr("helloworld"))
        self.assertEqual(r.content, b"helloworld")