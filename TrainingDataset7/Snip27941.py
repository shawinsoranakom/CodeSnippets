def test_constructor(self):
        """
        Tests assigning an image field through the model's constructor.
        """
        p = self.PersonModel(name="Joe", mugshot=self.file1)
        self.check_dimensions(p, 4, 8)
        p.save()
        self.check_dimensions(p, 4, 8)