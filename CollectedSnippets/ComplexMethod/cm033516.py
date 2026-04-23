def test_truthy_inputs(value: object, test: str, expected: bool, extra: Extra | None) -> None:
    """Ensure test plugins return the expected bool result, not just a truthy/falsey value."""
    test_invocation = test

    if extra:
        test_args = extra.args or []
        test_args.extend(f'{k}={v}' for k, v in (extra.kwargs or {}).items())
        test_invocation += '(' + ', '.join(str(arg) for arg in test_args) + ')'

    expression = f'{value} is {test_invocation}'

    with emits_warnings(deprecation_pattern=[]):
        result = Templar(variables=extra.variables if extra else None).evaluate_expression(trust_as_template(expression))

    assert result is expected