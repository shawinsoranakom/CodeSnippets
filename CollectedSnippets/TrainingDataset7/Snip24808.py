def test_file_interface(self):
        r = HttpResponse()
        r.write(b"hello")
        self.assertEqual(r.tell(), 5)
        r.write("привет")
        self.assertEqual(r.tell(), 17)

        r = HttpResponse(["abc"])
        r.write("def")
        self.assertEqual(r.tell(), 6)
        self.assertEqual(r.content, b"abcdef")

        # with Content-Encoding header
        r = HttpResponse()
        r.headers["Content-Encoding"] = "winning"
        r.write(b"abc")
        r.write(b"def")
        self.assertEqual(r.content, b"abcdef")