def validate_class(class_node: ast.ClassDef):
    attr_docs = get_attr_docs(class_node)

    for stmt in class_node.body:
        # A field is defined as a class variable that has a type annotation.
        if isinstance(stmt, ast.AnnAssign):
            # Skip ClassVar and InitVar
            # see https://docs.python.org/3/library/dataclasses.html#class-variables
            # and https://docs.python.org/3/library/dataclasses.html#init-only-variables
            if (
                isinstance(stmt.annotation, ast.Subscript)
                and isinstance(stmt.annotation.value, ast.Name)
                and stmt.annotation.value.id in {"ClassVar", "InitVar"}
            ):
                continue

            if isinstance(stmt.target, ast.Name):
                field_name = stmt.target.id
                if stmt.value is None:
                    fail(
                        f"Field '{field_name}' in {class_node.name} must have "
                        "a default value.",
                        stmt,
                    )

                if field_name not in attr_docs:
                    fail(
                        f"Field '{field_name}' in {class_node.name} must have "
                        "a docstring.",
                        stmt,
                    )

                if (
                    isinstance(stmt.annotation, ast.Subscript)
                    and isinstance(stmt.annotation.value, ast.Name)
                    and stmt.annotation.value.id == "Union"
                    and isinstance(stmt.annotation.slice, ast.Tuple)
                ):
                    args = stmt.annotation.slice.elts
                    literal_args = [
                        arg
                        for arg in args
                        if isinstance(arg, ast.Subscript)
                        and isinstance(arg.value, ast.Name)
                        and arg.value.id == "Literal"
                    ]
                    if len(literal_args) > 1:
                        fail(
                            f"Field '{field_name}' in {class_node.name} must "
                            "use a single "
                            "Literal type. Please use 'Literal[Literal1, "
                            "Literal2]' instead of 'Union[Literal1, Literal2]'"
                            ".",
                            stmt,
                        )