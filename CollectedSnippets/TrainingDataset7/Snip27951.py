def test_create(self):
        p = self.PersonModel.objects.create(mugshot=self.file1, headshot=self.file2)
        self.check_dimensions(p, 4, 8)
        self.check_dimensions(p, 8, 4, "headshot")