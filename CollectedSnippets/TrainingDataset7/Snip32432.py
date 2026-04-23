def test_all_files_less_verbose(self):
        """
        findstatic returns all candidate files if run without --first and -v0.
        """
        result = call_command(
            "findstatic", "test/file.txt", verbosity=0, stdout=StringIO()
        )
        lines = [line.strip() for line in result.split("\n")]
        self.assertEqual(len(lines), 2)
        self.assertIn("project", lines[0])
        self.assertIn("apps", lines[1])