def minimum_squares_to_represent_a_number(number: int) -> int:
    if number != int(number):
        raise ValueError("the value of input must be a natural number")
    if number < 0:
        raise ValueError("the value of input must not be a negative number")
    if number == 0:
        return 1
    answers = [-1] * (number + 1)
    answers[0] = 0
    for i in range(1, number + 1):
        answer = sys.maxsize
        root = int(math.sqrt(i))
        for j in range(1, root + 1):
            current_answer = 1 + answers[i - (j**2)]
            answer = min(answer, current_answer)
        answers[i] = answer
    return answers[number]
