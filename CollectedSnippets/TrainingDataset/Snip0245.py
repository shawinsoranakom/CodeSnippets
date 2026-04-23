def _validator(
    rotpos: RotorPositionT, rotsel: RotorSelectionT, pb: str
) -> tuple[RotorPositionT, RotorSelectionT, dict[str, str]]:
   

    if (unique_rotsel := len(set(rotsel))) < 3:
        msg = f"Please use 3 unique rotors (not {unique_rotsel})"
        raise Exception(msg)

    rotorpos1, rotorpos2, rotorpos3 = rotpos
    if not 0 < rotorpos1 <= len(abc):
        msg = f"First rotor position is not within range of 1..26 ({rotorpos1}"
        raise ValueError(msg)
    if not 0 < rotorpos2 <= len(abc):
        msg = f"Second rotor position is not within range of 1..26 ({rotorpos2})"
        raise ValueError(msg)
    if not 0 < rotorpos3 <= len(abc):
        msg = f"Third rotor position is not within range of 1..26 ({rotorpos3})"
        raise ValueError(msg)

    pbdict = _plugboard(pb)

    return rotpos, rotsel, pbdict

