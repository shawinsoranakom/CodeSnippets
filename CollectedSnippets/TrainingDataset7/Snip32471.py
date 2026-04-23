def test_summary_multiple_conflicts(self):
        """
        Summary shows correct count for multiple conflicts.
        """
        with tempfile.TemporaryDirectory() as static_dir:
            duplicate1 = os.path.join(static_dir, "test", "file.txt")
            os.makedirs(os.path.dirname(duplicate1))
            with open(duplicate1, "w+") as f:
                f.write("duplicate of file.txt")
            duplicate2 = os.path.join(static_dir, "test", "file1.txt")
            with open(duplicate2, "w+") as f:
                f.write("duplicate of file1.txt")
            duplicate3 = os.path.join(static_dir, "test", "nonascii.css")
            shutil.copy2(duplicate1, duplicate3)

            with self.settings(STATICFILES_DIRS=[static_dir]):
                output = self._collectstatic_output(clear=True, verbosity=1)
            self.assertIn("3 skipped due to conflict", output)