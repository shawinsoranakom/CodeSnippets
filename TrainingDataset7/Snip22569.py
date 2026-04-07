def test_fix_os_paths(self):
        self.assertEqual(fix_os_paths(self.path), ("/filepathfield_test_dir/"))