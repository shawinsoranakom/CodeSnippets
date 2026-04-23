def parse_copy_source_range_header(copy_source_range: str, object_size: int) -> ObjectRange:
    """
    Takes a CopySourceRange parameter, and returns a dataclass containing the necessary information to return only a slice of an
    S3 object. The validation is much stricter than `parse_range_header`
    :param copy_source_range: a CopySourceRange parameter for UploadCopyPart
    :param object_size: the requested S3 object total size
    :raises InvalidArgument if the CopySourceRanger parameter does not follow validation
    :return: ObjectRange
    """
    last = object_size - 1
    try:
        _, rspec = copy_source_range.split("=")
    except ValueError:
        raise InvalidArgument(
            "The x-amz-copy-source-range value must be of the form bytes=first-last where first and last are the zero-based offsets of the first and last bytes to copy",
            ArgumentName="x-amz-copy-source-range",
            ArgumentValue=copy_source_range,
        )
    if "," in rspec:
        raise InvalidArgument(
            "The x-amz-copy-source-range value must be of the form bytes=first-last where first and last are the zero-based offsets of the first and last bytes to copy",
            ArgumentName="x-amz-copy-source-range",
            ArgumentValue=copy_source_range,
        )

    try:
        begin, end = [int(i) if i else None for i in rspec.split("-")]
    except ValueError:
        # if we can't parse the Range header, S3 just treat the request as a non-range request
        raise InvalidArgument(
            "The x-amz-copy-source-range value must be of the form bytes=first-last where first and last are the zero-based offsets of the first and last bytes to copy",
            ArgumentName="x-amz-copy-source-range",
            ArgumentValue=copy_source_range,
        )

    if begin is None or end is None or begin > end:
        raise InvalidArgument(
            "The x-amz-copy-source-range value must be of the form bytes=first-last where first and last are the zero-based offsets of the first and last bytes to copy",
            ArgumentName="x-amz-copy-source-range",
            ArgumentValue=copy_source_range,
        )

    if begin > last:
        # Treat as non-range request if after the logic is applied
        raise InvalidRequest(
            "The specified copy range is invalid for the source object size",
        )
    elif end > last:
        raise InvalidArgument(
            f"Range specified is not valid for source object of size: {object_size}",
            ArgumentName="x-amz-copy-source-range",
            ArgumentValue=copy_source_range,
        )

    return ObjectRange(
        content_range=f"bytes {begin}-{end}/{object_size}",
        content_length=end - begin + 1,
        begin=begin,
        end=end,
    )