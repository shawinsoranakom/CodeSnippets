def moles_to_pressure(volume: float, moles: float, temperature: float) -> float:

    return round(float((moles * 0.0821 * temperature) / (volume)))
