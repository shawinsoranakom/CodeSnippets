def test_assignment_to_None(self):
        """
        Assigning ImageField to None clears dimensions.
        """
        p = self.PersonModel(name="Joe", mugshot=self.file1)
        self.check_dimensions(p, 4, 8)

        # If image assigned to None, dimension fields should be cleared.
        p.mugshot = None
        self.check_dimensions(p, None, None)

        p.mugshot = self.file2
        self.check_dimensions(p, 8, 4)