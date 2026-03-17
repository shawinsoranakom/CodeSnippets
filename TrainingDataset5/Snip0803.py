def builtin_voltage(
    donor_conc: float, 
    acceptor_conc: float, 
    intrinsic_conc: float, 
) -> float:

    if donor_conc <= 0:
        raise ValueError("Donor concentration should be positive")
    elif acceptor_conc <= 0:
        raise ValueError("Acceptor concentration should be positive")
    elif intrinsic_conc <= 0:
        raise ValueError("Intrinsic concentration should be positive")
    elif donor_conc <= intrinsic_conc:
        raise ValueError(
            "Donor concentration should be greater than intrinsic concentration"
        )
    elif acceptor_conc <= intrinsic_conc:
        raise ValueError(
            "Acceptor concentration should be greater than intrinsic concentration"
        )
    else:
        return (
            Boltzmann
            * T
            * log((donor_conc * acceptor_conc) / intrinsic_conc**2)
            / physical_constants["electron volt"][0]
        )
