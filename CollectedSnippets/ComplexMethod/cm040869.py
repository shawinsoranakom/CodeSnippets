def get_failed_precondition_copy_source(
    request: CopyObjectRequest, last_modified: datetime.datetime, etag: ETag
) -> str | None:
    """
    Validate if the source object LastModified and ETag matches a precondition, and if it does, return the failed
    precondition
    # see https://docs.aws.amazon.com/AmazonS3/latest/API/API_CopyObject.html
    :param request: the CopyObjectRequest
    :param last_modified: source object LastModified
    :param etag: source object ETag
    :return str: the failed precondition to raise
    """
    last_modified = second_resolution_datetime(last_modified)
    if (cs_if_match := request.get("CopySourceIfMatch")) and etag.strip('"') != cs_if_match.strip(
        '"'
    ):
        return "x-amz-copy-source-If-Match"

    elif (
        cs_if_unmodified_since := request.get("CopySourceIfUnmodifiedSince")
    ) and last_modified > second_resolution_datetime(cs_if_unmodified_since):
        return "x-amz-copy-source-If-Unmodified-Since"

    elif (cs_if_none_match := request.get("CopySourceIfNoneMatch")) and etag.strip(
        '"'
    ) == cs_if_none_match.strip('"'):
        return "x-amz-copy-source-If-None-Match"

    elif (
        cs_if_modified_since := request.get("CopySourceIfModifiedSince")
    ) and last_modified <= second_resolution_datetime(cs_if_modified_since) < datetime.datetime.now(
        tz=_gmt_zone_info
    ):
        return "x-amz-copy-source-If-Modified-Since"