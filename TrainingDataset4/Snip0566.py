def infix_2_prefix(infix: str) -> str:
    reversed_infix = list(infix[::-1])

    for i in range(len(reversed_infix)):
        if reversed_infix[i] == "(":
            reversed_infix[i] = ")"
        elif reversed_infix[i] == ")":
            reversed_infix[i] = "(" 
    return (infix_2_postfix("".join(reversed_infix)))[::-1]
