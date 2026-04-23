def test_port_reassigned(self):
        """When starting a new Streamlit session, it will run on port 8501 by default. If 8501 is
        not available, it will use the next available port.
        """

        out_one, out_two = self.run_double_proc(
            f"streamlit run --server.headless=true {REPO_ROOT}/examples/file_uploader.py",
            f"streamlit run --server.headless=true {REPO_ROOT}/examples/file_uploader.py",
        )

        assert ":8501" in out_one, f"Incorrect port. See output:\n{out_one}"
        assert ":8502" in out_two, f"Incorrect port. See output:\n{out_two}"