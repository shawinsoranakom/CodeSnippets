def test_assignment(self):
        p = self.PersonModel()
        self.check_dimensions(p, None, None, "mugshot")
        self.check_dimensions(p, None, None, "headshot")

        p.mugshot = self.file1
        self.check_dimensions(p, 4, 8, "mugshot")
        self.check_dimensions(p, None, None, "headshot")
        p.headshot = self.file2
        self.check_dimensions(p, 4, 8, "mugshot")
        self.check_dimensions(p, 8, 4, "headshot")

        # Clear the ImageFields one at a time.
        p.mugshot = None
        self.check_dimensions(p, None, None, "mugshot")
        self.check_dimensions(p, 8, 4, "headshot")
        p.headshot = None
        self.check_dimensions(p, None, None, "mugshot")
        self.check_dimensions(p, None, None, "headshot")