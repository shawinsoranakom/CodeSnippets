def test_no_warning_at_verbosity_1(self):
        """
        There is no individual warning at verbosity 1, but summary is shown.
        """
        with tempfile.TemporaryDirectory() as static_dir:
            duplicate = os.path.join(static_dir, "test", "file.txt")
            os.mkdir(os.path.dirname(duplicate))
            with open(duplicate, "w+") as f:
                f.write("duplicate of file.txt")

            with self.settings(STATICFILES_DIRS=[static_dir]):
                output = self._collectstatic_output(clear=True, verbosity=1)
            self.assertNotIn(self.warning_string, output)
            self.assertIn("1 skipped due to conflict", output)