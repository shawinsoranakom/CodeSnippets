def test_file_get_created_time(self):
        """
        File storage returns a datetime for the creation time of a file.
        """
        self.assertFalse(self.storage.exists("test.file"))

        f = ContentFile("custom contents")
        f_name = self.storage.save("test.file", f)
        self.addCleanup(self.storage.delete, f_name)

        path = self.storage.path(f_name)
        ctime = self.storage.get_created_time(f_name)

        self.assertAlmostEqual(
            ctime,
            datetime.datetime.fromtimestamp(os.path.getctime(path)),
            delta=datetime.timedelta(seconds=1),
        )
        self.assertAlmostEqual(
            ctime,
            timezone.now(),
            delta=datetime.timedelta(seconds=1),
        )