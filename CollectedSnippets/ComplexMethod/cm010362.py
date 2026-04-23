def mask_list(
    mask: list[bool], inp: list[Any], other: list[Any] | None = None
) -> list[Any]:
    # Masks elements on an `inp` list.
    # If other is None, then the elements of the `inp` list where the mask is False are removed
    # If other is not None, then the elements of the `inp` list where the mask is False are
    # replaced with the elements of the `other` list
    if len(mask) != len(inp):
        raise AssertionError(
            f"The length of the mask ({len(mask)}) needs to be identical to the length of the input ({len(inp)})"
        )
    if other is not None:
        if len(inp) != len(other):
            raise AssertionError(
                f"If an input and an other list is provided, they need to have the same length ({len(inp)} != {len(other)})"
            )
        return [i if m else o for m, i, o in zip(mask, inp, other)]
    else:
        return [i for m, i in zip(mask, inp) if m]