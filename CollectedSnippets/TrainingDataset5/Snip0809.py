def electric_conductivity(
    conductivity: float,
    electron_conc: float,
    mobility: float,
) -> tuple[str, float]:
    if (conductivity, electron_conc, mobility).count(0) != 1:
        raise ValueError("You cannot supply more or less than 2 values")
    elif conductivity < 0:
        raise ValueError("Conductivity cannot be negative")
    elif electron_conc < 0:
        raise ValueError("Electron concentration cannot be negative")
    elif mobility < 0:
        raise ValueError("mobility cannot be negative")
    elif conductivity == 0:
        return (
            "conductivity",
            mobility * electron_conc * ELECTRON_CHARGE,
        )
    elif electron_conc == 0:
        return (
            "electron_conc",
            conductivity / (mobility * ELECTRON_CHARGE),
        )
    else:
        return (
            "mobility",
            conductivity / (electron_conc * ELECTRON_CHARGE),
        )
