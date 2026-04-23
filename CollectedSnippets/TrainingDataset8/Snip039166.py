def test_current_directory(self):
        with patch("os.environ", {"PYTHONPATH": "."}):
            self.assertTrue(
                file_util.file_in_pythonpath(
                    self._make_it_absolute("something/dir1/dir2/module")
                )
            )
            self.assertTrue(
                file_util.file_in_pythonpath(
                    self._make_it_absolute("something_else/module")
                )
            )
            self.assertFalse(
                file_util.file_in_pythonpath(
                    self._make_it_absolute("../something_else/module")
                )
            )