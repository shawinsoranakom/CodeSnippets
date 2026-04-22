def test_no_pythonpath(self):
        with patch("os.environ", {}) as d:
            self.assertFalse(
                file_util.file_in_pythonpath(
                    self._make_it_absolute("../something/dir1/dir2/module")
                )
            )