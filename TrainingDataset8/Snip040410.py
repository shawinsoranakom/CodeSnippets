def test_cli_defined_port(self):
        out = self.run_single_proc(
            f"streamlit run --server.headless=true --server.port=9999 {REPO_ROOT}/examples/file_uploader.py",
        )

        assert ":9999" in out, f"Incorrect port. See output:\n{out}"