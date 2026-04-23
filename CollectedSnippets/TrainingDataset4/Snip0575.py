def evaluate_recursive(expression: list[str]):
    op = expression.pop(0)
    if is_operand(op):
        return int(op)

    operation = operators[op]

    a = evaluate_recursive(expression)
    b = evaluate_recursive(expression)
    return operation(a, b)
