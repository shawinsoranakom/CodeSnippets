def electric_power(voltage: float, current: float, power: float) -> tuple:
    if (voltage, current, power).count(0) != 1:
        raise ValueError("Exactly one argument must be 0")
    elif power < 0:
        raise ValueError(
            "Power cannot be negative in any electrical/electronics system"
        )
    elif voltage == 0:
        return Result("voltage", power / current)
    elif current == 0:
        return Result("current", power / voltage)
    elif power == 0:
        return Result("power", float(round(abs(voltage * current), 2)))
    else:
        raise AssertionError
