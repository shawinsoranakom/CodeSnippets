def test_collectstatic_emulation(self):
        """
        StaticLiveServerTestCase use of staticfiles' serve() allows it
        to discover app's static assets without having to collectstatic first.
        """
        with self.urlopen("/static/test/file.txt") as f:
            self.assertEqual(f.read().rstrip(b"\r\n"), b"In static directory.")