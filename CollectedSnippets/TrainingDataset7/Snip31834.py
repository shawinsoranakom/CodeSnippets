def test_static_files(self):
        with self.urlopen("/static/example_static_file.txt") as f:
            self.assertEqual(f.read().rstrip(b"\r\n"), b"example static file")