def test_setup_sh_source_build_uses_helper_latest_tag_only(self):
        """Shell source fallback should only use helper latest-tag resolution."""
        content = SETUP_SH.read_text()
        assert "--resolve-source-build" not in content
        assert "--resolve-install-tag" not in content
        assert (
            '--resolve-llama-tag latest --published-repo "ggml-org/llama.cpp"'
            in content
        )
        assert "--output-format json" in content
        assert "_RESOLVED_SOURCE_URL" in content
        assert "_RESOLVED_SOURCE_REF_KIND" in content
        assert "_RESOLVED_SOURCE_REF" in content