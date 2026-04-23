def test_size_method(self):
        """
        Bug #8534: FileField.size should not leave the file open.
        """
        p = self.PersonModel(name="Joan")
        p.mugshot.save("shot", self.file1)

        # Get a "clean" model instance
        p = self.PersonModel.objects.get(name="Joan")
        # It won't have an opened file.
        self.assertIs(p.mugshot.closed, True)

        # After asking for the size, the file should still be closed.
        p.mugshot.size
        self.assertIs(p.mugshot.closed, True)