def capacitor_parallel(capacitors: list[float]) -> float:
    sum_c = 0.0
    for index, capacitor in enumerate(capacitors):
        if capacitor < 0:
            msg = f"Capacitor at index {index} has a negative value!"
            raise ValueError(msg)
        sum_c += capacitor
    return sum_c
