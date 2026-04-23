def test_setup_sh_macos_arm64_uses_metal_flags(self):
        """Apple Silicon source builds should explicitly enable Metal like upstream."""
        content = SETUP_SH.read_text()
        assert "_IS_MACOS_ARM64=true" in content
        assert 'if [ "$_IS_MACOS_ARM64" = true ]; then' in content
        assert "-DGGML_METAL=ON" in content
        assert "-DGGML_METAL_EMBED_LIBRARY=ON" in content
        assert "-DGGML_METAL_USE_BF16=ON" in content
        assert "-DCMAKE_INSTALL_RPATH=@loader_path" in content
        assert "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON" in content