def test_field_save_and_delete_methods(self):
        p = self.PersonModel(name="Joe")
        p.mugshot.save("mug", self.file1)
        self.check_dimensions(p, 4, 8, "mugshot")
        self.check_dimensions(p, None, None, "headshot")
        p.headshot.save("head", self.file2)
        self.check_dimensions(p, 4, 8, "mugshot")
        self.check_dimensions(p, 8, 4, "headshot")

        # We can use save=True when deleting the image field with null=True
        # dimension fields and the other field has an image.
        p.headshot.delete(save=True)
        self.check_dimensions(p, 4, 8, "mugshot")
        self.check_dimensions(p, None, None, "headshot")
        p.mugshot.delete(save=False)
        self.check_dimensions(p, None, None, "mugshot")
        self.check_dimensions(p, None, None, "headshot")