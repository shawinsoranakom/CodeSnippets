def test_wrap_textiowrapper(self):
        content = "Café :)"
        r = HttpResponse()
        with io.TextIOWrapper(r, UTF8) as buf:
            buf.write(content)
        self.assertEqual(r.content, content.encode(UTF8))