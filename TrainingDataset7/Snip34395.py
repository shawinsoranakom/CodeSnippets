def test_notafile_error(self):
        # Windows raises PermissionError when trying to open a directory.
        with self.assertRaises(
            PermissionError if sys.platform == "win32" else IsADirectoryError
        ):
            self.engine.get_template("first")