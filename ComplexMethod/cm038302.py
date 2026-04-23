def get_parameter_value(val: ast.expr) -> Any:
    """Extract a Python literal value from an AST expression node.

    Handles constants, dicts, lists, and JSON-style name literals
    (null, true, false) that some models produce instead of Python
    literals (None, True, False).

    Raises:
        UnexpectedAstError: If the AST node is not a supported literal type.
    """
    if isinstance(val, ast.Constant):
        return val.value
    elif isinstance(val, ast.Dict):
        if not all(isinstance(k, ast.Constant) for k in val.keys):
            logger.warning(
                "Dict argument keys are not all literals: %s",
                ast.dump(val),
            )
            raise UnexpectedAstError("Dict tool call arguments must have literal keys")
        return {
            k.value: get_parameter_value(v)  # type: ignore
            for k, v in zip(val.keys, val.values)
        }
    elif isinstance(val, ast.List):
        return [get_parameter_value(v) for v in val.elts]
    elif isinstance(val, ast.Name) and val.id in _JSON_NAME_LITERALS:
        return _JSON_NAME_LITERALS[val.id]
    else:
        logger.warning(
            "Unsupported AST node type in tool call arguments: %s",
            ast.dump(val),
        )
        raise UnexpectedAstError("Tool call arguments must be literals")