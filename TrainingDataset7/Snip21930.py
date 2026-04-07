def test_directory_with_dot(self):
        """Regression test for #9610.

        If the directory name contains a dot and the file name doesn't, make
        sure we still mangle the file name instead of the directory name.
        """

        self.storage.save("dotted.path/test", ContentFile("1"))
        self.storage.save("dotted.path/test", ContentFile("2"))

        files = sorted(os.listdir(os.path.join(self.storage_dir, "dotted.path")))
        self.assertFalse(os.path.exists(os.path.join(self.storage_dir, "dotted_.path")))
        self.assertEqual(files[0], "test")
        self.assertRegex(files[1], "test_%s" % FILE_SUFFIX_REGEX)