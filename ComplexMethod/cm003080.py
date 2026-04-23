def load_stereo_chemical_props() -> tuple[
    Mapping[str, list[Bond]],
    Mapping[str, list[Bond]],
    Mapping[str, list[BondAngle]],
]:
    """Load stereo_chemical_props.txt into a nice structure.

    Load literature values for bond lengths and bond angles and translate bond angles into the length of the opposite
    edge of the triangle ("residue_virtual_bonds").

    Returns:
      residue_bonds: dict that maps resname --> list of Bond tuples residue_virtual_bonds: dict that maps resname -->
      list of Bond tuples residue_bond_angles: dict that maps resname --> list of BondAngle tuples
    """
    # TODO: this file should be downloaded in a setup script
    stereo_chemical_props = resources.read_text("openfold.resources", "stereo_chemical_props.txt")

    lines_iter = iter(stereo_chemical_props.splitlines())
    # Load bond lengths.
    residue_bonds: dict[str, list[Bond]] = {}
    next(lines_iter)  # Skip header line.
    for line in lines_iter:
        if line.strip() == "-":
            break
        bond, resname, bond_length, stddev = line.split()
        atom1, atom2 = bond.split("-")
        if resname not in residue_bonds:
            residue_bonds[resname] = []
        residue_bonds[resname].append(Bond(atom1, atom2, float(bond_length), float(stddev)))
    residue_bonds["UNK"] = []

    # Load bond angles.
    residue_bond_angles: dict[str, list[BondAngle]] = {}
    next(lines_iter)  # Skip empty line.
    next(lines_iter)  # Skip header line.
    for line in lines_iter:
        if line.strip() == "-":
            break
        bond, resname, angle_degree, stddev_degree = line.split()
        atom1, atom2, atom3 = bond.split("-")
        if resname not in residue_bond_angles:
            residue_bond_angles[resname] = []
        residue_bond_angles[resname].append(
            BondAngle(
                atom1,
                atom2,
                atom3,
                float(angle_degree) / 180.0 * np.pi,
                float(stddev_degree) / 180.0 * np.pi,
            )
        )
    residue_bond_angles["UNK"] = []

    def make_bond_key(atom1_name: str, atom2_name: str) -> str:
        """Unique key to lookup bonds."""
        return "-".join(sorted([atom1_name, atom2_name]))

    # Translate bond angles into distances ("virtual bonds").
    residue_virtual_bonds: dict[str, list[Bond]] = {}
    for resname, bond_angles in residue_bond_angles.items():
        # Create a fast lookup dict for bond lengths.
        bond_cache: dict[str, Bond] = {}
        for b in residue_bonds[resname]:
            bond_cache[make_bond_key(b.atom1_name, b.atom2_name)] = b
        residue_virtual_bonds[resname] = []
        for ba in bond_angles:
            bond1 = bond_cache[make_bond_key(ba.atom1_name, ba.atom2_name)]
            bond2 = bond_cache[make_bond_key(ba.atom2_name, ba.atom3name)]

            # Compute distance between atom1 and atom3 using the law of cosines
            # c^2 = a^2 + b^2 - 2ab*cos(gamma).
            gamma = ba.angle_rad
            length = np.sqrt(bond1.length**2 + bond2.length**2 - 2 * bond1.length * bond2.length * np.cos(gamma))

            # Propagation of uncertainty assuming uncorrelated errors.
            dl_outer = 0.5 / length
            dl_dgamma = (2 * bond1.length * bond2.length * np.sin(gamma)) * dl_outer
            dl_db1 = (2 * bond1.length - 2 * bond2.length * np.cos(gamma)) * dl_outer
            dl_db2 = (2 * bond2.length - 2 * bond1.length * np.cos(gamma)) * dl_outer
            stddev = np.sqrt(
                (dl_dgamma * ba.stddev) ** 2 + (dl_db1 * bond1.stddev) ** 2 + (dl_db2 * bond2.stddev) ** 2
            )
            residue_virtual_bonds[resname].append(Bond(ba.atom1_name, ba.atom3name, length, stddev))

    return (residue_bonds, residue_virtual_bonds, residue_bond_angles)