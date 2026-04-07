def test_random_bytes(self):
        """A random number of bytes is added to mitigate the BREACH attack."""
        with mock.patch(
            "django.utils.text.secrets.randbelow", autospec=True, return_value=3
        ):
            r = GZipMiddleware(self.get_response)(self.req)
        # The fourth byte of a gzip stream contains flags.
        self.assertEqual(r.content[3], gzip.FNAME)
        # A 3 byte filename "aaa" and a null byte are added.
        self.assertEqual(r.content[10:14], b"aaa\x00")
        self.assertEqual(self.decompress(r.content), self.compressible_string)