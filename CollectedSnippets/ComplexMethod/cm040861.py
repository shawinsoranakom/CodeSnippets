def parse_range_header(range_header: str, object_size: int) -> ObjectRange | None:
    """
    Takes a Range header, and returns a dataclass containing the necessary information to return only a slice of an
    S3 object. If the range header is invalid, we return None so that the request is treated as a regular request.
    :param range_header: a Range header
    :param object_size: the requested S3 object total size
    :return: ObjectRange or None if the Range header is invalid
    """
    last = object_size - 1
    try:
        _, rspec = range_header.split("=")
    except ValueError:
        return None
    if "," in rspec:
        return None

    try:
        begin, end = [int(i) if i else None for i in rspec.split("-")]
    except ValueError:
        # if we can't parse the Range header, S3 just treat the request as a non-range request
        return None

    if (begin is None and end == 0) or (begin is not None and begin > last):
        raise InvalidRange(
            "The requested range is not satisfiable",
            ActualObjectSize=str(object_size),
            RangeRequested=range_header,
        )

    if begin is not None:  # byte range
        end = last if end is None else min(end, last)
    elif end is not None:  # suffix byte range
        begin = object_size - min(end, object_size)
        end = last
    else:
        # Treat as non-range request
        return None

    if begin > min(end, last):
        # Treat as non-range request if after the logic is applied
        return None

    return ObjectRange(
        content_range=f"bytes {begin}-{end}/{object_size}",
        content_length=end - begin + 1,
        begin=begin,
        end=end,
    )