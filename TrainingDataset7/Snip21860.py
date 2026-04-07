def test_file_get_accessed_time(self):
        """
        File storage returns a Datetime object for the last accessed time of
        a file.
        """
        self.assertFalse(self.storage.exists("test.file"))

        f = ContentFile("custom contents")
        f_name = self.storage.save("test.file", f)
        self.addCleanup(self.storage.delete, f_name)

        path = self.storage.path(f_name)
        atime = self.storage.get_accessed_time(f_name)

        self.assertAlmostEqual(
            atime,
            datetime.datetime.fromtimestamp(os.path.getatime(path)),
            delta=datetime.timedelta(seconds=1),
        )
        self.assertAlmostEqual(
            atime,
            timezone.now(),
            delta=datetime.timedelta(seconds=1),
        )