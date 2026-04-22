def test_pydoc(self):
        """Test that we can run pydoc on the streamlit package"""
        cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            # Run the script as a separate process to make sure that
            # the currently loaded modules do not affect the test result.
            output = subprocess.check_output(
                [sys.executable, "-m", "pydoc", "streamlit"]
            ).decode()
            self.assertIn("Help on package streamlit:", output)
        finally:
            os.chdir(cwd)