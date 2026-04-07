def test_open_returns_self(self):
        """
        FieldField.open() returns self so it can be used as a context manager.
        """
        d = Document.objects.create(myfile="something.txt")
        # Replace the FileField's file with an in-memory ContentFile, so that
        # open() doesn't write to disk.
        d.myfile.file = ContentFile(b"", name="bla")
        self.assertEqual(d.myfile, d.myfile.open())