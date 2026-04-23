def test_no_optional_dependency_classification(self):
        """Test that the simplified analyzer doesn't classify any dependencies as optional."""
        from lfx.custom.dependency_analyzer import analyze_dependencies

        # Code with various import patterns that previously might have been considered optional
        code = """
import os
try:
    import package_a
    HAS_A = True
except ImportError:
    HAS_A = False

try:
    import package_b
except ImportError:
    pass

try:
    from package_c import something
except (ImportError, ModuleNotFoundError):
    something = None
"""
        deps = analyze_dependencies(code, resolve_versions=False)

        # Should find external dependencies only (stdlib filtered out)
        dep_names = [d["name"] for d in deps]
        assert "package_a" in dep_names
        assert "package_b" in dep_names
        assert "package_c" in dep_names

        # Stdlib imports should be filtered out
        assert "os" not in dep_names

        # All found dependencies should be external (not local)
        for dep in deps:
            assert not dep["is_local"], f"Dependency {dep['name']} should not be local"