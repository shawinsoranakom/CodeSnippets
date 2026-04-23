def lexical_order(max_number: int) -> Iterator[int]:
    stack = [1]

    while stack:
        num = stack.pop()
        if num > max_number:
            continue

        yield num
        if (num % 10) != 9:
            stack.append(num + 1)

        stack.append(num * 10)
