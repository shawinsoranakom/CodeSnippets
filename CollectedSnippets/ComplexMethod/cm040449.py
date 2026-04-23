def _least_upper_bound(*nodes):
    """Compute the least upper bound of a set of nodes.

    Args:
        nodes: sequence of entries from dtypes + weak_types

    Returns:
        The type representing the least upper bound of the input nodes on the
        promotion lattice.
    """
    # This function computes the least upper bound of a set of nodes N within a
    # partially ordered set defined by the lattice generated above.
    # Given a partially ordered set S, let the set of upper bounds of n ∈ S be
    #   UB(n) ≡ {m ∈ S | n ≤ m}
    # Further, for a set of nodes N ⊆ S, let the set of common upper bounds be
    # given by
    #   CUB(N) ≡ {a ∈ S | ∀ b ∈ N: a ∈ UB(b)}
    # Then the least upper bound of N is defined as
    #   LUB(N) ≡ {c ∈ CUB(N) | ∀ d ∈ CUB(N), c ≤ d}
    # The definition of an upper bound implies that
    #   c ≤ d if and only if d ∈ UB(c),
    # so the LUB can be expressed:
    #   LUB(N) = {c ∈ CUB(N) | ∀ d ∈ CUB(N): d ∈ UB(c)}
    # or, equivalently:
    #   LUB(N) = {c ∈ CUB(N) | CUB(N) ⊆ UB(c)}
    # By definition, LUB(N) has a cardinality of 1 for a partially ordered set.
    # Note a potential algorithmic shortcut: from the definition of CUB(N),
    # we have
    #   ∀ c ∈ N: CUB(N) ⊆ UB(c)
    # So if N ∩ CUB(N) is nonempty, if follows that LUB(N) = N ∩ CUB(N).
    N = set(nodes)
    UB = LATTICE_UPPER_BOUNDS
    try:
        bounds = [UB[n] for n in N]
    except KeyError:
        dtype = next(n for n in N if n not in UB)
        raise ValueError(
            f"{dtype=} is not a valid dtype for Keras type promotion."
        )
    CUB = set.intersection(*bounds)
    LUB = (CUB & N) or {c for c in CUB if CUB.issubset(UB[c])}
    if len(LUB) == 1:
        return LUB.pop()
    elif len(LUB) == 0:
        msg = (
            f"Input dtypes {tuple(str(n) for n in nodes)} have no available "
            "implicit dtype promotion path. Try explicitly casting inputs to "
            "the desired output type."
        )
        raise ValueError(msg)
    else:
        # If we get here, it means the lattice is ill-formed.
        raise ValueError(
            f"Internal Type Promotion error: {nodes} do not have a unique "
            f"least upper bound on the specified lattice; options are {LUB}. "
            "This is an unexpected error in Keras's internal logic; "
            "please report it to the maintainers."
        )