def test_is_rdna_source_has_rdna2(self):
        """is_rdna() should include RDNA2 architectures."""
        utils_path = PACKAGE_ROOT / "unsloth" / "kernels" / "utils.py"
        source = utils_path.read_text()
        func_start = source.find("def is_rdna()")
        func_body = source[func_start : source.find("\ndef ", func_start + 1)]
        assert "gfx1030" in func_body
        assert "gfx1031" in func_body
        assert "gfx1032" in func_body
        assert "gfx1033" in func_body
        assert "gfx1034" in func_body
        assert "gfx1035" in func_body
        assert "gfx1036" in func_body