def test_stream_interface(self):
        r = HttpResponse("asdf")
        self.assertEqual(r.getvalue(), b"asdf")

        r = HttpResponse()
        self.assertIs(r.writable(), True)
        r.writelines(["foo\n", "bar\n", "baz\n"])
        self.assertEqual(r.content, b"foo\nbar\nbaz\n")