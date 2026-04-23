def electrical_impedance(
    resistance: float, reactance: float, impedance: float
) -> dict[str, float]:
    if (resistance, reactance, impedance).count(0) != 1:
        raise ValueError("One and only one argument must be 0")
    if resistance == 0:
        return {"resistance": sqrt(pow(impedance, 2) - pow(reactance, 2))}
    elif reactance == 0:
        return {"reactance": sqrt(pow(impedance, 2) - pow(resistance, 2))}
    elif impedance == 0:
        return {"impedance": sqrt(pow(resistance, 2) + pow(reactance, 2))}
    else:
        raise ValueError("Exactly one argument must be 0")
