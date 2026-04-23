def generate_parentheses_iterative(length: int) -> list:
    
    result = []
    stack = []

    stack.append(("", 0, 0))

    while stack:
        current_combination, open_count, close_count = stack.pop()

        if len(current_combination) == 2 * length:
            result.append(current_combination)

        if open_count < length:
            stack.append((current_combination + "(", open_count + 1, close_count))

        if close_count < open_count:
            stack.append((current_combination + ")", open_count, close_count + 1))

    return result
