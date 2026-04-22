def test_relative_main_file(self):
        """Test that we get abs dir path when __main__.__file__ is script file name only."""

        ch = _CodeHasher()

        # We don't want empty string returned:
        self.assertNotEqual(ch._get_main_script_directory(), "")

        # During testing, __main__.__file__ has not modified so we expect current
        # working dir:
        self.assertEqual(ch._get_main_script_directory(), os.getcwd())