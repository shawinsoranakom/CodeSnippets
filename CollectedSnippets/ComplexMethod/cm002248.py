def _extract_definitions(
        self, file_path: Path, relative_to: Path | None = None, model_hint: str | None = None
    ) -> tuple[dict[str, str], dict[str, str], dict[str, list[str]], dict[str, str]]:
        """
        Extract class and function definitions from a Python file.

        Args:
            file_path (`Path`): Path to the Python file to parse.
            relative_to (`Path` or `None`): Base path for computing relative identifiers.
            model_hint (`str` or `None`): Model name hint for sanitization.

        Returns:
            `tuple[dict[str, str], dict[str, str], dict[str, list[str]], dict[str, str]]`: A tuple containing:
                - definitions_raw: Mapping of identifiers to raw source code
                - definitions_sanitized: Mapping of identifiers to sanitized source code
                - definitions_tokens: Mapping of identifiers to sorted token lists
                - definitions_kind: Mapping of identifiers to either "class" or "function"
        """
        definitions_raw = {}
        definitions_sanitized = {}
        definitions_tokens = {}
        definitions_kind = {}
        source = file_path.read_text(encoding="utf-8")
        lines = source.splitlines()
        tree = ast.parse(source)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                segment = ast.get_source_segment(source, node)
                if segment is None and hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    start = max(0, node.lineno - 1)
                    end = node.end_lineno
                    segment = "\n".join(lines[start:end])
                if segment:
                    identifier = (
                        f"{file_path.relative_to(relative_to)}:{node.name}"
                        if relative_to
                        else f"{file_path.name}:{node.name}"
                    )
                    definitions_raw[identifier] = segment
                    sanitized = _sanitize_for_embedding(segment, model_hint, node.name)
                    definitions_sanitized[identifier] = sanitized
                    definitions_tokens[identifier] = sorted(_tokenize(sanitized))
                    if isinstance(node, ast.ClassDef):
                        definitions_kind[identifier] = "class"
                    else:
                        definitions_kind[identifier] = "function"
        return definitions_raw, definitions_sanitized, definitions_tokens, definitions_kind