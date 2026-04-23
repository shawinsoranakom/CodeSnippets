def pressure_and_volume_to_temperature(
    pressure: float, moles: float, volume: float
) -> float:
    return round(float((pressure * volume) / (0.0821 * moles)))
