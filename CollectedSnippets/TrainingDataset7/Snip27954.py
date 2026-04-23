def test_dimensions(self):
        """
        Dimensions are updated correctly in various situations.
        """
        p = self.PersonModel(name="Joe")

        # Dimensions should get set for the saved file.
        p.mugshot.save("mug", self.file1)
        p.headshot.save("head", self.file2)
        self.check_dimensions(p, 4, 8, "mugshot")
        self.check_dimensions(p, 8, 4, "headshot")

        # Test dimensions after fetching from database.
        p = self.PersonModel.objects.get(name="Joe")
        # Bug 11084: Dimensions should not get recalculated if file is
        # coming from the database. We test this by checking if the file
        # was opened.
        self.assertIs(p.mugshot.was_opened, False)
        self.assertIs(p.headshot.was_opened, False)
        self.check_dimensions(p, 4, 8, "mugshot")
        self.check_dimensions(p, 8, 4, "headshot")
        # After checking dimensions on the image fields, the files will
        # have been opened.
        self.assertIs(p.mugshot.was_opened, True)
        self.assertIs(p.headshot.was_opened, True)
        # Dimensions should now be cached, and if we reset was_opened and
        # check dimensions again, the file should not have opened.
        p.mugshot.was_opened = False
        p.headshot.was_opened = False
        self.check_dimensions(p, 4, 8, "mugshot")
        self.check_dimensions(p, 8, 4, "headshot")
        self.assertIs(p.mugshot.was_opened, False)
        self.assertIs(p.headshot.was_opened, False)

        # If we assign a new image to the instance, the dimensions should
        # update.
        p.mugshot = self.file2
        p.headshot = self.file1
        self.check_dimensions(p, 8, 4, "mugshot")
        self.check_dimensions(p, 4, 8, "headshot")
        # Dimensions were recalculated, and hence file should have opened.
        self.assertIs(p.mugshot.was_opened, True)
        self.assertIs(p.headshot.was_opened, True)