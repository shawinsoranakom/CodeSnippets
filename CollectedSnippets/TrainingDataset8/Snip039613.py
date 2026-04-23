def test_absolute_main_file(self):
        """Test that we get abs dir path when __main__.__file__ relative path."""

        import pathlib

        ch = _CodeHasher()

        # When __main__.__file__ is absolute path to script, we expect parent dir to be
        # returned:
        self.assertEqual(
            ch._get_main_script_directory(), str(pathlib.Path(self.abs_path).parent)
        )