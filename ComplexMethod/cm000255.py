def infix_to_postfix(expression_str: str) -> str:
    """
    >>> infix_to_postfix("(1*(2+3)+4))")
    Traceback (most recent call last):
        ...
    ValueError: Mismatched parentheses
    >>> infix_to_postfix("")
    ''
    >>> infix_to_postfix("3+2")
    '3 2 +'
    >>> infix_to_postfix("(3+4)*5-6")
    '3 4 + 5 * 6 -'
    >>> infix_to_postfix("(1+2)*3/4-5")
    '1 2 + 3 * 4 / 5 -'
    >>> infix_to_postfix("a+b*c+(d*e+f)*g")
    'a b c * + d e * f + g * +'
    >>> infix_to_postfix("x^y/(5*z)+2")
    'x y ^ 5 z * / 2 +'
    >>> infix_to_postfix("2^3^2")
    '2 3 2 ^ ^'
    """
    if not balanced_parentheses(expression_str):
        raise ValueError("Mismatched parentheses")
    stack: Stack[str] = Stack()
    postfix = []
    for char in expression_str:
        if char.isalpha() or char.isdigit():
            postfix.append(char)
        elif char == "(":
            stack.push(char)
        elif char == ")":
            while not stack.is_empty() and stack.peek() != "(":
                postfix.append(stack.pop())
            stack.pop()
        else:
            while True:
                if stack.is_empty():
                    stack.push(char)
                    break

                char_precedence = precedence(char)
                tos_precedence = precedence(stack.peek())

                if char_precedence > tos_precedence:
                    stack.push(char)
                    break
                if char_precedence < tos_precedence:
                    postfix.append(stack.pop())
                    continue
                # Precedences are equal
                if associativity(char) == "RL":
                    stack.push(char)
                    break
                postfix.append(stack.pop())

    while not stack.is_empty():
        postfix.append(stack.pop())
    return " ".join(postfix)