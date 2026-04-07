def test_noname_file_get_size(self):
        self.assertEqual(File(BytesIO(b"A file with no name")).size, 19)