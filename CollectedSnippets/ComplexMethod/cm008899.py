def test_grep_with_special_characters(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Grep should treat special characters in the pattern literally."""
        if not self.has_sync:
            pytest.skip("Sync tests not supported.")

        base_dir = self.sandbox_path("grep_special", root_dir=sandbox_test_root)
        sandbox_backend.execute(f"mkdir -p {_quote(base_dir)}")
        sandbox_backend.write(
            f"{base_dir}/special.txt", "Price: $100\nPath: /usr/bin\nPattern: [a-z]*"
        )

        dollar = sandbox_backend.grep("$100", path=base_dir)
        brackets = sandbox_backend.grep("[a-z]*", path=base_dir)

        assert dollar.error is None
        assert dollar.matches is not None
        assert len(dollar.matches) == 1
        assert "$100" in dollar.matches[0]["text"]

        assert brackets.error is None
        assert brackets.matches is not None
        assert len(brackets.matches) == 1
        assert "[a-z]*" in brackets.matches[0]["text"]