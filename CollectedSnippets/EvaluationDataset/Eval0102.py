def moles_to_volume(pressure: float, moles: float, temperature: float) -> float:

    return round(float((moles * 0.0821 * temperature) / (pressure)))
