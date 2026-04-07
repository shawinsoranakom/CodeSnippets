def test_file_multiple(self):
        f = MultipleFileField()
        files = [
            SimpleUploadedFile("name1", b"Content 1"),
            SimpleUploadedFile("name2", b"Content 2"),
        ]
        self.assertEqual(f.clean(files), files)