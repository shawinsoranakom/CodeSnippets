def evaluate(expression):
    stack = []

    for c in expression.split()[::-1]:
        if is_operand(c):
            stack.append(int(c))

        else:
            o1 = stack.pop()
            o2 = stack.pop()
            stack.append(operators[c](o1, o2))

    return stack.pop()
