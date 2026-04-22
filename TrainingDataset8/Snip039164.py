def test_python_path_absolute(self):
        with patch("os.environ", {"PYTHONPATH": self._make_it_absolute("something")}):
            self.assertTrue(
                file_util.file_in_pythonpath(
                    self._make_it_absolute("something/dir1/dir2/module")
                )
            )
            self.assertFalse(
                file_util.file_in_pythonpath(
                    self._make_it_absolute("something_else/module")
                )
            )
            self.assertFalse(
                file_util.file_in_pythonpath(
                    self._make_it_absolute("../something/dir1/dir2/module")
                )
            )