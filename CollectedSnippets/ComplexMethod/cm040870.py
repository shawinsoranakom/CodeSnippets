def validate_failed_precondition(
    request: GetObjectRequest | HeadObjectRequest, last_modified: datetime.datetime, etag: ETag
) -> None:
    """
    Validate if the object LastModified and ETag matches a precondition, and if it does, return the failed
    precondition
    :param request: the GetObjectRequest or HeadObjectRequest
    :param last_modified: S3 object LastModified
    :param etag: S3 object ETag
    :raises PreconditionFailed
    :raises NotModified, 304 with an empty body
    """
    precondition_failed = None
    # last_modified needs to be rounded to a second so that strict equality can be enforced from a RFC1123 header
    last_modified = second_resolution_datetime(last_modified)
    if (if_match := request.get("IfMatch")) and etag != if_match.strip('"'):
        precondition_failed = "If-Match"

    elif (
        if_unmodified_since := request.get("IfUnmodifiedSince")
    ) and last_modified > second_resolution_datetime(if_unmodified_since):
        precondition_failed = "If-Unmodified-Since"

    if precondition_failed:
        raise PreconditionFailed(
            "At least one of the pre-conditions you specified did not hold",
            Condition=precondition_failed,
        )

    if ((if_none_match := request.get("IfNoneMatch")) and etag == if_none_match.strip('"')) or (
        (if_modified_since := request.get("IfModifiedSince"))
        and last_modified
        <= second_resolution_datetime(if_modified_since)
        < datetime.datetime.now(tz=_gmt_zone_info)
    ):
        raise CommonServiceException(
            message="Not Modified",
            code="NotModified",
            status_code=304,
        )