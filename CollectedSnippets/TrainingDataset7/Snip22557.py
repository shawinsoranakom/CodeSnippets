def test_filefield_2(self):
        f = FileField(max_length=5)
        with self.assertRaisesMessage(
            ValidationError,
            "'Ensure this filename has at most 5 characters (it has 18).'",
        ):
            f.clean(SimpleUploadedFile("test_maxlength.txt", b"hello world"))
        self.assertEqual("files/test1.pdf", f.clean("", "files/test1.pdf"))
        self.assertEqual("files/test2.pdf", f.clean(None, "files/test2.pdf"))
        self.assertIsInstance(
            f.clean(SimpleUploadedFile("name", b"Some File Content")),
            SimpleUploadedFile,
        )