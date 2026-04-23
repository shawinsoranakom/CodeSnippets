def test_all_files(self):
        """
        findstatic returns all candidate files if run without --first and -v1.
        """
        result = call_command(
            "findstatic", "test/file.txt", verbosity=1, stdout=StringIO()
        )
        lines = [line.strip() for line in result.split("\n")]
        self.assertEqual(
            len(lines), 3
        )  # three because there is also the "Found <file> here" line
        self.assertIn("project", lines[1])
        self.assertIn("apps", lines[2])