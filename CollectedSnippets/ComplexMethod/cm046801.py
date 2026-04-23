def test_binary_env_linux_has_binary_parent(self):
        """The Linux branch of binary_env should include binary_path.parent."""
        content = MODULE_PATH.read_text()
        # Find the binary_env function
        in_func = False
        in_linux = False
        found = False
        for line in content.splitlines():
            if "def binary_env(" in line:
                in_func = True
            elif in_func and line and not line[0].isspace() and "def " in line:
                break
            if in_func and "host.is_linux" in line:
                in_linux = True
            if in_linux and "binary_path.parent" in line:
                found = True
                break
        assert found, "binary_path.parent not found in Linux branch of binary_env"