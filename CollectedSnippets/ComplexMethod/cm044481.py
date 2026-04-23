def get_label(index: int, num_identities: int, next_identity: bool = False) -> str:
    """Obtain the label for the given current index. Labels start at A at index 0. Values roll.

    Parameters
    ----------
    index
        The index of the current label
    num_identities
        The number of identities that belong to the label set
    next_identity
        ``True`` to return the next identity for the given index. Default: ``False``

    Returns
    -------
    The current or next label. Labels go A-Z,0-9,a-z
    """
    identities = [chr(i) for i in range(65, 65 + 26)]
    if num_identities > len(identities):
        identities += [chr(i) for i in range(48, 48 + 10)]
    if num_identities > len(identities):
        identities += [chr(i) for i in range(97, 97 + 26)]
    if num_identities > len(identities):
        raise FaceswapError(f"Too many identities: {num_identities}. Max: {len(identities)}")
    identities = identities[:num_identities]
    index = index % num_identities
    if not next_identity:
        return identities[index]
    index += 1 if index + 1 < num_identities else -index
    return identities[index]