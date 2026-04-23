def test_conflicting_port(self):
        out_one, out_two = self.run_double_proc(
            f"streamlit run --server.headless=true {REPO_ROOT}/examples/file_uploader.py",
            f"streamlit run --server.headless=true --server.port=8501 {REPO_ROOT}/examples/file_uploader.py",
        )

        assert ":8501" in out_one, f"Incorrect port. See output:\n{out_one}"
        assert (
            "Port 8501 is already in use" in out_two
        ), f"Incorrect conflict. See output:\n{out_one}"