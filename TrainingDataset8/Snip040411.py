def test_config_toml_defined_port(self):
        with open(CONFIG_FILE_PATH, "w") as file:
            file.write("[server]\n  port=8888")

        out = self.run_single_proc(
            f"streamlit run --server.headless=true {REPO_ROOT}/examples/file_uploader.py",
        )

        assert ":8888" in out, f"Incorrect port. See output:\n{out}"