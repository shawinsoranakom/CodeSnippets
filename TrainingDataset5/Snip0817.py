def resistor_series(resistors: list[float]) -> float:
    sum_r = 0.00
    for index, resistor in enumerate(resistors):
        sum_r += resistor
        if resistor < 0:
            msg = f"Resistor at index {index} has a negative value!"
            raise ValueError(msg)
    return sum_r
