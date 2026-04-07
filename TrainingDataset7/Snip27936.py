def test_instantiate_missing(self):
        """
        If the underlying file is unavailable, still create instantiate the
        object without error.
        """
        p = self.PersonModel(name="Joan")
        p.mugshot.save("shot", self.file1)
        p = self.PersonModel.objects.get(name="Joan")
        path = p.mugshot.path
        shutil.move(path, path + ".moved")
        self.PersonModel.objects.get(name="Joan")