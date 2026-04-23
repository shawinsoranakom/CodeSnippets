def get_pdb_headers(prot: Protein, chain_id: int = 0) -> list[str]:
    pdb_headers: list[str] = []

    remark = prot.remark
    if remark is not None:
        pdb_headers.append(f"REMARK {remark}")

    parents = prot.parents
    parents_chain_index = prot.parents_chain_index
    if parents is not None and parents_chain_index is not None:
        parents = [p for i, p in zip(parents_chain_index, parents) if i == chain_id]

    if parents is None or len(parents) == 0:
        parents = ["N/A"]

    pdb_headers.append(f"PARENT {' '.join(parents)}")

    return pdb_headers