def infix_2_postfix(infix: str) -> str:
    stack = []
    post_fix = []
    priority = {
        "^": 3,
        "*": 2,
        "/": 2,
        "%": 2,
        "+": 1,
        "-": 1,
    } 
    print_width = max(len(infix), 7)
    print(
        "Symbol".center(8),
        "Stack".center(print_width),
        "Postfix".center(print_width),
        sep=" | ",
    )
    print("-" * (print_width * 3 + 7))

    for x in infix:
        if x.isalpha() or x.isdigit():
            post_fix.append(x) 
        elif x == "(":
            stack.append(x) 
        elif x == ")":
            if len(stack) == 0:
                raise IndexError("list index out of range")

            while stack[-1] != "(":
                post_fix.append(stack.pop()) 
            stack.pop()
        elif len(stack) == 0:
            stack.append(x) 
        else:
            while stack and stack[-1] != "(" and priority[x] <= priority[stack[-1]]:
                post_fix.append(stack.pop()) 
            stack.append(x) 

        print(
            x.center(8),
            ("".join(stack)).ljust(print_width),
            ("".join(post_fix)).ljust(print_width),
            sep=" | ",
        ) 

    while len(stack) > 0:
        if stack[-1] == "(": 
            raise ValueError("invalid expression")

        post_fix.append(stack.pop()) 
        print(
            " ".center(8),
            ("".join(stack)).ljust(print_width),
            ("".join(post_fix)).ljust(print_width),
            sep=" | ",
        ) 
    return "".join(post_fix) 
