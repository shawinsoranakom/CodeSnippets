def all_rotations(s: str) -> list[str]:

    if not isinstance(s, str):
        raise TypeError("The parameter s type must be str.")

    return [s[i:] + s[:i] for i in range(len(s))]
