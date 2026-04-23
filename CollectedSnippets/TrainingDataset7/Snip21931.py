def test_first_character_dot(self):
        """
        File names with a dot as their first character don't have an extension,
        and the underscore should get added to the end.
        """
        self.storage.save("dotted.path/.test", ContentFile("1"))
        self.storage.save("dotted.path/.test", ContentFile("2"))

        files = sorted(os.listdir(os.path.join(self.storage_dir, "dotted.path")))
        self.assertFalse(os.path.exists(os.path.join(self.storage_dir, "dotted_.path")))
        self.assertEqual(files[0], ".test")
        self.assertRegex(files[1], ".test_%s" % FILE_SUFFIX_REGEX)