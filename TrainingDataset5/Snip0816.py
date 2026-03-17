def resistor_parallel(resistors: list[float]) -> float:

    first_sum = 0.00
    for index, resistor in enumerate(resistors):
        if resistor <= 0:
            msg = f"Resistor at index {index} has a negative or zero value!"
            raise ValueError(msg)
        first_sum += 1 / float(resistor)
    return 1 / first_sum
