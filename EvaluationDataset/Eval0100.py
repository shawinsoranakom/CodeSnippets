def molarity_to_normality(nfactor: int, moles: float, volume: float) -> float:

    return round(float(moles / volume) * nfactor)
