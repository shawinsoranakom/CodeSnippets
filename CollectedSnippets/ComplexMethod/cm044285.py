def _parse_docstring_params(func: Callable | None) -> dict[str, str]:
        """Parse parameter descriptions from a NumPy-style docstring.

        Parameters
        ----------
        func : Optional[Callable]
            The function whose docstring to parse.

        Returns
        -------
        dict[str, str]
            Mapping of parameter name to its description text.
        """
        if func is None:
            return {}
        doc = inspect.getdoc(func) or ""
        if not doc:
            return {}

        # Find the Parameters section
        params_match = re.search(
            r"^\s*Parameters\s*\n\s*[-=~`]{3,}",
            doc,
            re.MULTILINE,
        )
        if not params_match:
            return {}

        # Extract text after the dashes line
        after_header = doc[params_match.end() :]
        # Find the next section header (e.g., Returns, Raises, Examples, Notes)
        next_section = re.search(
            r"^\s*[A-Z][a-z]+\s*\n\s*[-=~`]{3,}",
            after_header,
            re.MULTILINE,
        )
        params_text = (
            after_header[: next_section.start()] if next_section else after_header
        )

        result: dict[str, str] = {}
        current_name: str | None = None
        current_desc_lines: list[str] = []

        for line in params_text.splitlines():
            # Match a parameter line like "param_name : type" or "param_name: type"
            param_match = re.match(r"^\s{0,4}(\w+)\s*:\s*", line)
            if param_match:
                # Save previous parameter
                if current_name is not None:
                    result[current_name] = " ".join(current_desc_lines).strip()
                current_name = param_match.group(1)
                current_desc_lines = []
            elif current_name is not None and line.strip():
                current_desc_lines.append(line.strip())

        # Save last parameter
        if current_name is not None:
            result[current_name] = " ".join(current_desc_lines).strip()

        return result