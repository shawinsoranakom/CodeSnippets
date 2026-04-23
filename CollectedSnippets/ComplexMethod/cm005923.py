def test_no_deprecated_langchain_imports(self):
        """Test that no component uses deprecated langchain import paths.

        This specifically catches issues like the Qdrant bug where
        'from langchain.embeddings.base import Embeddings' was used instead of
        'from langchain_core.embeddings import Embeddings'.

        Uses AST parsing to scan all Python files for deprecated patterns.
        """
        import ast
        from pathlib import Path

        try:
            import lfx

            lfx_path = Path(lfx.__file__).parent
        except ImportError:
            pytest.skip("lfx package not found")

        components_path = lfx_path / "components"
        if not components_path.exists():
            pytest.skip("lfx.components directory not found")

        deprecated_imports = []

        # Known deprecated import patterns
        deprecated_patterns = [
            ("langchain.embeddings.base", "langchain_core.embeddings"),
            ("langchain.llms.base", "langchain_core.language_models.llms"),
            ("langchain.chat_models.base", "langchain_core.language_models.chat_models"),
            ("langchain.schema", "langchain_core.messages"),
            ("langchain.vectorstores", "langchain_community.vectorstores"),
            ("langchain.document_loaders", "langchain_community.document_loaders"),
            ("langchain.text_splitter", "langchain_text_splitters"),
        ]

        # Walk through all Python files in components
        for py_file in components_path.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        module = node.module or ""

                        # Check against deprecated patterns
                        for deprecated, replacement in deprecated_patterns:
                            if module.startswith(deprecated):
                                relative_path = py_file.relative_to(lfx_path)
                                deprecated_imports.append(
                                    f"{relative_path}:{node.lineno}: "
                                    f"Uses deprecated '{deprecated}' - should use '{replacement}'"
                                )

            except Exception:  # noqa: S112
                # Skip files that can't be parsed
                continue

        if deprecated_imports:
            failure_msg = (
                f"Found {len(deprecated_imports)} deprecated langchain imports.\n\n"
                f"Deprecated imports:\n" + "\n".join(f"  • {imp}" for imp in deprecated_imports) + "\n\n"
                "Please update to use current import paths."
            )
            pytest.fail(failure_msg)