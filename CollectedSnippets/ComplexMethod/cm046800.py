def test_setup_ps1_source_build_uses_helper_latest_tag_only(self):
        """PS1 source fallback should only use helper latest-tag resolution."""
        content = SETUP_PS1.read_text()
        assert "--resolve-source-build" not in content
        assert "--resolve-install-tag" not in content
        assert (
            '"--resolve-llama-tag", "latest", "--published-repo", "ggml-org/llama.cpp"'
            in content
        )
        assert '--output-format", "json"' in content
        assert "$ResolvedSourceUrl" in content
        assert "$ResolvedSourceRefKind" in content
        assert "$ResolvedSourceRef" in content