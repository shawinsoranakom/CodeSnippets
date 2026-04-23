def test_delete_when_missing(self):
        """
        Bug #8175: correctly delete an object where the file no longer
        exists on the file system.
        """
        p = self.PersonModel(name="Fred")
        p.mugshot.save("shot", self.file1)
        os.remove(p.mugshot.path)
        p.delete()