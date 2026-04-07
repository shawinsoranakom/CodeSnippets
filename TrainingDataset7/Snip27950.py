def test_constructor(self):
        p = self.PersonModel(mugshot=self.file1, headshot=self.file2)
        self.check_dimensions(p, 4, 8, "mugshot")
        self.check_dimensions(p, 8, 4, "headshot")
        p.save()
        self.check_dimensions(p, 4, 8, "mugshot")
        self.check_dimensions(p, 8, 4, "headshot")