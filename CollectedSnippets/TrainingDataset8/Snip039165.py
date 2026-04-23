def test_python_path_mixed(self):
        with patch(
            "os.environ",
            {
                "PYTHONPATH": os.pathsep.join(
                    [self._make_it_absolute("something"), "something"]
                )
            },
        ):
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