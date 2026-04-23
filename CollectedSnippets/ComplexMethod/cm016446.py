def _generate_inner_class_stub(
        cls,
        name: str,
        attr: type,
        indent: str = "    ",
        type_tracker: Optional[TypeTracker] = None,
    ) -> list[str]:
        """Generate stub for an inner class."""
        stub_lines = []
        stub_lines.append(f"{indent}class {name}Sync:")

        # Add docstring if available
        if hasattr(attr, "__doc__") and attr.__doc__:
            stub_lines.extend(
                cls._format_docstring_for_stub(attr.__doc__, f"{indent}    ")
            )

        # Add __init__ if it exists
        if hasattr(attr, "__init__"):
            try:
                init_method = getattr(attr, "__init__")
                init_sig = inspect.signature(init_method)

                # Try to get type hints
                try:
                    from typing import get_type_hints
                    init_hints = get_type_hints(init_method)
                except Exception:
                    init_hints = {}

                # Format parameters
                params_str = cls._format_method_parameters(
                    init_sig, type_hints=init_hints, type_tracker=type_tracker
                )
                # Add __init__ docstring if available (before the method)
                if hasattr(init_method, "__doc__") and init_method.__doc__:
                    stub_lines.extend(
                        cls._format_docstring_for_stub(
                            init_method.__doc__, f"{indent}    "
                        )
                    )
                stub_lines.append(
                    f"{indent}    def __init__({params_str}) -> None: ..."
                )
            except (ValueError, TypeError):
                stub_lines.append(
                    f"{indent}    def __init__(self, *args, **kwargs) -> None: ..."
                )

        # Add methods to the inner class
        has_methods = False
        for method_name, method in sorted(
            inspect.getmembers(attr, predicate=inspect.isfunction)
        ):
            if method_name.startswith("_"):
                continue

            has_methods = True
            try:
                # Add method docstring if available (before the method signature)
                if method.__doc__:
                    stub_lines.extend(
                        cls._format_docstring_for_stub(method.__doc__, f"{indent}    ")
                    )

                method_sig = cls._generate_method_signature(
                    method_name, method, is_async=True, type_tracker=type_tracker
                )
                stub_lines.append(f"{indent}    {method_sig}")
            except (ValueError, TypeError):
                stub_lines.append(
                    f"{indent}    def {method_name}(self, *args, **kwargs): ..."
                )

        if not has_methods:
            stub_lines.append(f"{indent}    pass")

        return stub_lines