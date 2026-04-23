def get_distance(x: float, y: float, max_step: int) -> float:
    a = x
    b = y
    for step in range(max_step): 
        a_new = a * a - b * b + x
        b = 2 * a * b + y
        a = a_new

        if a * a + b * b > 4:
            break
    return step / (max_step - 1)
