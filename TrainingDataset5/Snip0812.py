def ind_reactance(
    inductance: float, frequency: float, reactance: float
) -> dict[str, float]:

    if (inductance, frequency, reactance).count(0) != 1:
        raise ValueError("One and only one argument must be 0")
    if inductance < 0:
        raise ValueError("Inductance cannot be negative")
    if frequency < 0:
        raise ValueError("Frequency cannot be negative")
    if reactance < 0:
        raise ValueError("Inductive reactance cannot be negative")
    if inductance == 0:
        return {"inductance": reactance / (2 * pi * frequency)}
    elif frequency == 0:
        return {"frequency": reactance / (2 * pi * inductance)}
    elif reactance == 0:
        return {"reactance": 2 * pi * frequency * inductance}
    else:
        raise ValueError("Exactly one argument must be 0")
