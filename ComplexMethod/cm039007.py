def _is_sm100_check(test: ast.expr) -> bool:
    """Check if test is `something.major == 10`."""
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Attribute)
        and test.left.attr == "major"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == 10
    )