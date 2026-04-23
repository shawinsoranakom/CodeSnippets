def carrier_concentration(
    electron_conc: float,
    hole_conc: float,
    intrinsic_conc: float,
) -> tuple:
    if (electron_conc, hole_conc, intrinsic_conc).count(0) != 1:
        raise ValueError("You cannot supply more or less than 2 values")
    elif electron_conc < 0:
        raise ValueError("Electron concentration cannot be negative in a semiconductor")
    elif hole_conc < 0:
        raise ValueError("Hole concentration cannot be negative in a semiconductor")
    elif intrinsic_conc < 0:
        raise ValueError(
            "Intrinsic concentration cannot be negative in a semiconductor"
        )
    elif electron_conc == 0:
        return (
            "electron_conc",
            intrinsic_conc**2 / hole_conc,
        )
    elif hole_conc == 0:
        return (
            "hole_conc",
            intrinsic_conc**2 / electron_conc,
        )
    elif intrinsic_conc == 0:
        return (
            "intrinsic_conc",
            (electron_conc * hole_conc) ** 0.5,
        )
    else:
        return (-1, -1)
