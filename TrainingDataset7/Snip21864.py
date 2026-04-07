def test_file_get_modified_time(self):
        """
        File storage returns a datetime for the last modified time of a file.
        """
        self.assertFalse(self.storage.exists("test.file"))

        f = ContentFile("custom contents")
        f_name = self.storage.save("test.file", f)
        self.addCleanup(self.storage.delete, f_name)

        path = self.storage.path(f_name)
        mtime = self.storage.get_modified_time(f_name)

        self.assertAlmostEqual(
            mtime,
            datetime.datetime.fromtimestamp(os.path.getmtime(path)),
            delta=datetime.timedelta(seconds=1),
        )
        self.assertAlmostEqual(
            mtime,
            timezone.now(),
            delta=datetime.timedelta(seconds=1),
        )