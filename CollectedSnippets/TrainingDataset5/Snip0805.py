def capacitor_series(capacitors: list[float]) -> float:
    first_sum = 0.0
    for index, capacitor in enumerate(capacitors):
        if capacitor <= 0:
            msg = f"Capacitor at index {index} has a negative or zero value!"
            raise ValueError(msg)
        first_sum += 1 / capacitor
    return 1 / first_sum
