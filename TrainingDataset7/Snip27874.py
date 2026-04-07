def test_unique_when_same_filename(self):
        """
        A FileField with unique=True shouldn't allow two instances with the
        same name to be saved.
        """
        Document.objects.create(myfile="something.txt")
        with self.assertRaises(IntegrityError):
            Document.objects.create(myfile="something.txt")