def __init__(
        self,
        expression: str,
        *,
        allow_underscore: bool = False,
        allow_duplicates: bool = False,
    ) -> None:
        """Parse the expression and store relevant metadata.

        Args:
            expression (str): the `einops`-pattern to parse
            allow_underscore (bool): whether to allow axis identifier names to begin with an underscore
            allow_duplicates (bool): whether to allow an identifier to appear more than once in the expression
        """
        self.has_ellipsis: bool = False
        self.has_ellipsis_parenthesized: bool | None = None
        self.identifiers: set[str | AnonymousAxis] = set()
        # that's axes like 2, 3, 4 or 5. Axes with size 1 are exceptional and replaced with empty composition
        self.has_non_unitary_anonymous_axes: bool = False
        # composition keeps structure of composite axes, see how different corner cases are handled in tests
        self.composition: list[list[str | AnonymousAxis] | str] = []
        if "." in expression:
            if "..." not in expression:
                raise ValueError(
                    "Expression may contain dots only inside ellipsis (...)"
                )
            if str.count(expression, "...") != 1 or str.count(expression, ".") != 3:
                raise ValueError(
                    "Expression may contain dots only inside ellipsis (...); only one ellipsis for tensor "
                )
            expression = expression.replace("...", _ellipsis)
            self.has_ellipsis = True

        bracket_group: list[str | AnonymousAxis] | None = None

        def add_axis_name(x: str) -> None:
            if x in self.identifiers:
                if not (allow_underscore and x == "_") and not allow_duplicates:
                    raise ValueError(
                        f"Indexing expression contains duplicate dimension '{x}'"
                    )
            if x == _ellipsis:
                self.identifiers.add(_ellipsis)
                if bracket_group is None:
                    self.composition.append(_ellipsis)
                    self.has_ellipsis_parenthesized = False
                else:
                    bracket_group.append(_ellipsis)
                    self.has_ellipsis_parenthesized = True
            else:
                is_number = str.isdecimal(x)
                if is_number and int(x) == 1:
                    # handling the case of anonymous axis of length 1
                    if bracket_group is None:
                        self.composition.append([])
                    else:
                        pass  # no need to think about 1s inside parenthesis
                    return
                is_axis_name, reason = self.check_axis_name_return_reason(
                    x, allow_underscore=allow_underscore
                )
                if not (is_number or is_axis_name):
                    raise ValueError(f"Invalid axis identifier: {x}\n{reason}")
                axis_name: str | AnonymousAxis = AnonymousAxis(x) if is_number else x
                self.identifiers.add(axis_name)
                if is_number:
                    self.has_non_unitary_anonymous_axes = True
                if bracket_group is None:
                    self.composition.append([axis_name])
                else:
                    bracket_group.append(axis_name)

        current_identifier = None
        for char in expression:
            if char in "() ":
                if current_identifier is not None:
                    add_axis_name(current_identifier)
                current_identifier = None
                if char == "(":
                    if bracket_group is not None:
                        raise ValueError(
                            "Axis composition is one-level (brackets inside brackets not allowed)"
                        )
                    bracket_group = []
                elif char == ")":
                    if bracket_group is None:
                        raise ValueError("Brackets are not balanced")
                    self.composition.append(bracket_group)
                    bracket_group = None
            elif str.isalnum(char) or char in ["_", _ellipsis]:
                if current_identifier is None:
                    current_identifier = char
                else:
                    current_identifier += char
            else:
                raise ValueError(f"Unknown character '{char}'")

        if bracket_group is not None:
            raise ValueError(f"Imbalanced parentheses in expression: '{expression}'")
        if current_identifier is not None:
            add_axis_name(current_identifier)