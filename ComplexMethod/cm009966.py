def dims(
    n: int | None = None, sizes: list[int | None] | None = None
) -> Dim | tuple[Dim, ...]:
    """
    Create and return one or more Dim objects.

    Uses bytecode inspection to determine variable names when possible.

    Args:
        n (int, optional): The number of dimensions to create. Can be omitted if sizes is specified.
        sizes (List[Optional[int]], optional): A list the same size as the number of dimensions to be
          created, specifying each dimensions size, or None to leave the size unset.

    Returns:
        Union[Dim, Tuple[Dim, ...]]: Single Dim if n=1, tuple of Dims otherwise.

    Examples:
        >>> batch, channel, width, height = dims(4)
        >>> batch, channel, width, height = dims(sizes=[None, 3, 224, 224])
        >>> single_dim = dims(1)
    """
    specified_ndims = -1
    found_ndims = 0

    # Parse arguments
    if sizes is not None:
        specified_ndims = len(sizes)
    if n is not None:
        specified_ndims = n

    # Use bytecode inspection
    frame = inspect.currentframe()
    if frame is None:
        raise RuntimeError("Unable to get current frame")
    frame = frame.f_back
    try:
        if frame is None:
            raise RuntimeError("Unable to get caller frame")
        code = frame.f_code
        lasti = frame.f_lasti

        decoder = _PyInstDecoder(code, lasti)

        if sys.version_info >= (3, 11):
            if decoder.opcode() == "PRECALL":
                decoder.next()

        # Move to next instruction after the call
        decoder.next()

        # Determine number of dimensions from bytecode
        if _relevant_op(decoder.opcode()):
            found_ndims = 1
        elif decoder.opcode() == "UNPACK_SEQUENCE":
            found_ndims = decoder.oparg()
            decoder.next()  # Move past UNPACK_SEQUENCE

        if specified_ndims == -1:
            if found_ndims == 0:
                raise SyntaxError(
                    "dims() must be assigned to a sequence of variable names or have argument n specified"
                )
            specified_ndims = found_ndims

        if found_ndims != specified_ndims:
            found_ndims = 0

        def genobject(i: int) -> Dim:
            nonlocal found_ndims
            name = None
            if i < found_ndims:
                name = decoder.name()

            if not name:
                name = f"d{i}"
                found_ndims = 0
            else:
                decoder.next()  # Move to next STORE instruction

            size = sizes[i] if sizes is not None else None
            return _create_dim(name, size)

        # Validate sizes parameter
        if sizes is not None and len(sizes) != specified_ndims:
            raise ValueError(f"expected {specified_ndims} sizes but found {len(sizes)}")

        if specified_ndims == 1:
            return genobject(0)

        result = []
        for i in range(specified_ndims):
            result.append(genobject(i))

        return tuple(result)

    finally:
        del frame