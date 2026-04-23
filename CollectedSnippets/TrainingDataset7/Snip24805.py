def test_iter_content(self):
        r = HttpResponse(["abc", "def", "ghi"])
        self.assertEqual(r.content, b"abcdefghi")

        # test iter content via property
        r = HttpResponse()
        r.content = ["idan", "alex", "jacob"]
        self.assertEqual(r.content, b"idanalexjacob")

        r = HttpResponse()
        r.content = [1, 2, 3]
        self.assertEqual(r.content, b"123")

        # test odd inputs
        r = HttpResponse()
        r.content = ["1", "2", 3, "\u079e"]
        # '\xde\x9e' == unichr(1950).encode()
        self.assertEqual(r.content, b"123\xde\x9e")

        # .content can safely be accessed multiple times.
        r = HttpResponse(iter(["hello", "world"]))
        self.assertEqual(r.content, r.content)
        self.assertEqual(r.content, b"helloworld")
        # __iter__ can safely be called multiple times (#20187).
        self.assertEqual(b"".join(r), b"helloworld")
        self.assertEqual(b"".join(r), b"helloworld")
        # Accessing .content still works.
        self.assertEqual(r.content, b"helloworld")

        # Accessing .content also works if the response was iterated first.
        r = HttpResponse(iter(["hello", "world"]))
        self.assertEqual(b"".join(r), b"helloworld")
        self.assertEqual(r.content, b"helloworld")

        # Additional content can be written to the response.
        r = HttpResponse(iter(["hello", "world"]))
        self.assertEqual(r.content, b"helloworld")
        r.write("!")
        self.assertEqual(r.content, b"helloworld!")