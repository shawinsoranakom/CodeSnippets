def test_file_url(self):
        """
        File storage returns a url to access a given file from the web.
        """
        self.assertEqual(
            self.storage.url("test.file"), self.storage.base_url + "test.file"
        )

        # should encode special chars except ~!*()'
        # like encodeURIComponent() JavaScript function do
        self.assertEqual(
            self.storage.url(r"~!*()'@#$%^&*abc`+ =.file"),
            "/test_media_url/~!*()'%40%23%24%25%5E%26*abc%60%2B%20%3D.file",
        )
        self.assertEqual(self.storage.url("ab\0c"), "/test_media_url/ab%00c")

        # should translate os path separator(s) to the url path separator
        self.assertEqual(
            self.storage.url("""a/b\\c.file"""), "/test_media_url/a/b/c.file"
        )

        # #25905: remove leading slashes from file names to prevent unsafe url
        # output
        self.assertEqual(self.storage.url("/evil.com"), "/test_media_url/evil.com")
        self.assertEqual(self.storage.url(r"\evil.com"), "/test_media_url/evil.com")
        self.assertEqual(self.storage.url("///evil.com"), "/test_media_url/evil.com")
        self.assertEqual(self.storage.url(r"\\\evil.com"), "/test_media_url/evil.com")

        self.assertEqual(self.storage.url(None), "/test_media_url/")