def test_noname_file_default_name(self):
        self.assertIsNone(File(BytesIO(b"A file with no name")).name)