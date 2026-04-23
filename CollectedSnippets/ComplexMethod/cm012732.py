def get_accumulator_dtype(
    input_torch_dtypes: list[torch.dtype],
) -> torch.dtype | None:
    """
    Given a pair of input torch dtypes, returns the inferred accumulator torch dtype.
    """

    assert OrderedSet(input_torch_dtypes) <= XW_DTYPES, (
        f"{input_torch_dtypes=} is not supported"
    )

    if len(input_torch_dtypes) != 2:
        return None

    if OrderedSet(input_torch_dtypes) == OrderedSet(
        [torch.float8_e5m2, torch.float8_e4m3fn]
    ):
        return torch.float

    torch_dtype = None
    if input_torch_dtypes[0] == input_torch_dtypes[1]:
        torch_dtype = input_torch_dtypes[0]
    else:
        size0 = torch.tensor([], dtype=input_torch_dtypes[0]).element_size()
        size1 = torch.tensor([], dtype=input_torch_dtypes[1]).element_size()
        if size0 > size1:
            dtype0, dtype1 = input_torch_dtypes
        else:
            dtype1, dtype0 = input_torch_dtypes
        if dtype0 in [torch.half, torch.bfloat16] and dtype1 in [
            torch.int8,
            torch.uint8,
        ]:
            torch_dtype = dtype0

    if torch_dtype in (
        torch.float16,
        torch.bfloat16,
        torch.float,
        torch.float8_e4m3fn,
        torch.float8_e5m2,
    ):
        accumulator_dtype = torch.float
    elif torch_dtype == torch.int8:
        accumulator_dtype = torch.int32
    else:
        raise NotImplementedError(f"Unsupported data types: {input_torch_dtypes=}")

    assert accumulator_dtype in ACCUMULATOR_DTYPES, (
        f"{accumulator_dtype=} is not supported"
    )
    return accumulator_dtype