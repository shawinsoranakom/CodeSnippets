def test_run_no_arguments(self):
        """streamlit run should fail if run with no arguments."""
        result = self.runner.invoke(cli, ["run"])
        self.assertNotEqual(0, result.exit_code)