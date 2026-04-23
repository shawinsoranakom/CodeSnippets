def _detect_reexport_pattern(cls, module_name: str) -> dict[str, str | None]:
        """Detect what kind of re-export pattern a module uses."""
        try:
            module = importlib.import_module(module_name)

            # Check if module has source code that mentions lfx
            source_file = getattr(module, "__file__", None)
            if source_file:
                try:
                    with Path(source_file).open() as f:
                        content = f.read()
                        if "from lfx" in content:
                            # Try to extract the lfx module being imported
                            patterns = [
                                r"from (lfx\.[.\w]+) import",
                                r"from (lfx\.[.\w]+) import \*",
                                r"import (lfx\.[.\w]+)",
                            ]
                            for pattern in patterns:
                                match = re.search(pattern, content)
                                if match:
                                    return {"type": "direct", "source": match.group(1)}

                        if "__getattr__" in content and "lfx" in content:
                            return {"type": "dynamic", "source": None}

                        # If we get here, file exists but no patterns matched
                        return {"type": "none", "source": None}

                except (OSError, UnicodeDecodeError):
                    return {"type": "none", "source": None}
            else:
                return {"type": "none", "source": None}

        except ImportError:
            return {"type": "import_error", "source": None}