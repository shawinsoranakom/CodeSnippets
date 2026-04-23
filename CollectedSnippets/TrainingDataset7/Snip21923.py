def test_race_condition(self):
        self.thread.start()
        self.save_file("conflict")
        self.thread.join()
        files = sorted(os.listdir(self.storage_dir))
        self.assertEqual(files[0], "conflict")
        self.assertRegex(files[1], "conflict_%s" % FILE_SUFFIX_REGEX)