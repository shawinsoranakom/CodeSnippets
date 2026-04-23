def test_filefield_1(self):
        f = FileField()
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("", "")
        self.assertEqual("files/test1.pdf", f.clean("", "files/test1.pdf"))
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None, "")
        self.assertEqual("files/test2.pdf", f.clean(None, "files/test2.pdf"))
        no_file_msg = "'No file was submitted. Check the encoding type on the form.'"
        file = SimpleUploadedFile(None, b"")
        file._name = ""
        with self.assertRaisesMessage(ValidationError, no_file_msg):
            f.clean(file)
        with self.assertRaisesMessage(ValidationError, no_file_msg):
            f.clean(file, "")
        self.assertEqual("files/test3.pdf", f.clean(None, "files/test3.pdf"))
        with self.assertRaisesMessage(ValidationError, no_file_msg):
            f.clean("some content that is not a file")
        with self.assertRaisesMessage(
            ValidationError, "'The submitted file is empty.'"
        ):
            f.clean(SimpleUploadedFile("name", None))
        with self.assertRaisesMessage(
            ValidationError, "'The submitted file is empty.'"
        ):
            f.clean(SimpleUploadedFile("name", b""))
        self.assertEqual(
            SimpleUploadedFile,
            type(f.clean(SimpleUploadedFile("name", b"Some File Content"))),
        )
        self.assertIsInstance(
            f.clean(
                SimpleUploadedFile(
                    "我隻氣墊船裝滿晒鱔.txt",
                    "मेरी मँडराने वाली नाव सर्पमीनों से भरी ह".encode(),
                )
            ),
            SimpleUploadedFile,
        )
        self.assertIsInstance(
            f.clean(
                SimpleUploadedFile("name", b"Some File Content"), "files/test4.pdf"
            ),
            SimpleUploadedFile,
        )