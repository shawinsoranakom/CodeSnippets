def get_failed_upload_part_copy_source_preconditions(
    request: UploadPartCopyRequest, last_modified: datetime.datetime, etag: ETag
) -> str | None:
    """
    Utility which parses the conditions from a S3 UploadPartCopy request.
    Note: The order in which these conditions are checked if used in conjunction matters

    :param UploadPartCopyRequest request: The S3 UploadPartCopy request.
    :param datetime last_modified: The time the source object was last modified.
    :param ETag etag: The ETag of the source object.

    :returns: The name of the failed precondition.
    """
    if_match = request.get("CopySourceIfMatch")
    if_none_match = request.get("CopySourceIfNoneMatch")
    if_unmodified_since = request.get("CopySourceIfUnmodifiedSince")
    if_modified_since = request.get("CopySourceIfModifiedSince")
    last_modified = second_resolution_datetime(last_modified)

    if if_match:
        if if_match.strip('"') != etag.strip('"'):
            return "x-amz-copy-source-If-Match"
        if if_modified_since and if_modified_since > last_modified:
            return "x-amz-copy-source-If-Modified-Since"
        # CopySourceIfMatch is unaffected by CopySourceIfUnmodifiedSince so return early
        if if_unmodified_since:
            return None

    if if_unmodified_since and second_resolution_datetime(if_unmodified_since) < last_modified:
        return "x-amz-copy-source-If-Unmodified-Since"

    if if_none_match and if_none_match.strip('"') == etag.strip('"'):
        return "x-amz-copy-source-If-None-Match"

    if if_modified_since and last_modified <= second_resolution_datetime(
        if_modified_since
    ) < datetime.datetime.now(tz=_gmt_zone_info):
        return "x-amz-copy-source-If-Modified-Since"