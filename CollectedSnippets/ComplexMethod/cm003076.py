def from_proteinnet_string(proteinnet_str: str) -> Protein:
    tag_re = r"(\[[A-Z]+\]\n)"
    tags: list[str] = [tag.strip() for tag in re.split(tag_re, proteinnet_str) if len(tag) > 0]
    groups: Iterator[tuple[str, list[str]]] = zip(tags[0::2], [l.split("\n") for l in tags[1::2]])

    atoms: list[str] = ["N", "CA", "C"]
    aatype = None
    atom_positions = None
    atom_mask = None
    for g in groups:
        if g[0] == "[PRIMARY]":
            seq = g[1][0].strip()
            # Replace unknown residues with "X" (strings are immutable, so convert to list first)
            seq = [char if char in residue_constants.restypes else "X" for char in seq]
            aatype = np.array(
                [residue_constants.restype_order.get(res_symbol, residue_constants.restype_num) for res_symbol in seq]
            )
        elif g[0] == "[TERTIARY]":
            tertiary: list[list[float]] = []
            for axis in range(3):
                tertiary.append(list(map(float, g[1][axis].split())))
            tertiary_np = np.array(tertiary)
            atom_positions = np.zeros((len(tertiary[0]) // 3, residue_constants.atom_type_num, 3)).astype(np.float32)
            for i, atom in enumerate(atoms):
                atom_positions[:, residue_constants.atom_order[atom], :] = np.transpose(tertiary_np[:, i::3])
            atom_positions *= PICO_TO_ANGSTROM
        elif g[0] == "[MASK]":
            mask = np.array(list(map({"-": 0, "+": 1}.get, g[1][0].strip())))
            atom_mask = np.zeros(
                (
                    len(mask),
                    residue_constants.atom_type_num,
                )
            ).astype(np.float32)
            for i, atom in enumerate(atoms):
                atom_mask[:, residue_constants.atom_order[atom]] = 1
            atom_mask *= mask[..., None]

    assert aatype is not None

    return Protein(
        atom_positions=atom_positions,
        atom_mask=atom_mask,
        aatype=aatype,
        residue_index=np.arange(len(aatype)),
        b_factors=None,
    )