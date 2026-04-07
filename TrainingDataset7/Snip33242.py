def test_truncate(self):
        uri = "http://31characteruri.com/test/"
        self.assertEqual(len(uri), 31)

        self.assertEqual(
            urlizetrunc(uri, 31),
            '<a href="http://31characteruri.com/test/" rel="nofollow">'
            "http://31characteruri.com/test/</a>",
        )

        self.assertEqual(
            urlizetrunc(uri, 30),
            '<a href="http://31characteruri.com/test/" rel="nofollow">'
            "http://31characteruri.com/tes…</a>",
        )

        self.assertEqual(
            urlizetrunc(uri, 1),
            '<a href="http://31characteruri.com/test/" rel="nofollow">…</a>',
        )