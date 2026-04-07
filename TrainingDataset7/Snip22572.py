def test_clean(self):
        f = FilePathField(path=self.path)
        msg = "'Select a valid choice. a.py is not one of the available choices.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("a.py")
        self.assertEqual(
            fix_os_paths(f.clean(self.path + "a.py")), "/filepathfield_test_dir/a.py"
        )