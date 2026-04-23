def test_media_files(self):
        with self.urlopen("/media/example_media_file.txt") as f:
            self.assertEqual(f.read().rstrip(b"\r\n"), b"example media file")