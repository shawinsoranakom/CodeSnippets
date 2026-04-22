def test_run_not_allowed_file_extension(self):
        """streamlit run should fail if a not allowed file extension is passed."""

        result = self.runner.invoke(cli, ["run", "file_name.doc"])

        self.assertNotEqual(0, result.exit_code)
        self.assertIn(
            "Streamlit requires raw Python (.py) files, not .doc.", result.output
        )