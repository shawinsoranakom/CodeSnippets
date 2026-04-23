def test_warning_at_verbosity_2(self):
        """
        There is a warning when there are duplicate destinations at verbosity
        2+.
        """
        with tempfile.TemporaryDirectory() as static_dir:
            duplicate = os.path.join(static_dir, "test", "file.txt")
            os.mkdir(os.path.dirname(duplicate))
            with open(duplicate, "w+") as f:
                f.write("duplicate of file.txt")

            with self.settings(STATICFILES_DIRS=[static_dir]):
                output = self._collectstatic_output(clear=True, verbosity=2)
            self.assertIn(self.warning_string, output)