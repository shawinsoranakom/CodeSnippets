def test_file_multiple_empty(self):
        f = MultipleFileField()
        files = [
            SimpleUploadedFile("empty", b""),
            SimpleUploadedFile("nonempty", b"Some Content"),
        ]
        msg = "'The submitted file is empty.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(files)
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(files[::-1])