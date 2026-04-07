def test_filefield_changed(self):
        """
        The value of data will more than likely come from request.FILES. The
        value of initial data will likely be a filename stored in the database.
        Since its value is of no use to a FileField it is ignored.
        """
        f = FileField()

        # No file was uploaded and no initial data.
        self.assertFalse(f.has_changed("", None))

        # A file was uploaded and no initial data.
        self.assertTrue(
            f.has_changed("", {"filename": "resume.txt", "content": "My resume"})
        )

        # A file was not uploaded, but there is initial data
        self.assertFalse(f.has_changed("resume.txt", None))

        # A file was uploaded and there is initial data (file identity is not
        # dealt with here)
        self.assertTrue(
            f.has_changed(
                "resume.txt", {"filename": "resume.txt", "content": "My resume"}
            )
        )