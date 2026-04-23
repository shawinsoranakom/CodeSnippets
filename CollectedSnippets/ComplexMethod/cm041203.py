def legacy_s3_rules(request: Request) -> ServiceModelIdentifier | None:
    """
    *Legacy* rules which allow us to fallback to S3 if no other service was matched.
    All rules which are implemented here should be removed once we make sure it would not break any use-cases.
    """

    path = request.path
    method = request.method

    # TODO The remaining rules here are special S3 rules - needs to be discussed how these should be handled.
    #      Some are similar to other rules and not that greedy, others are nearly general fallbacks.
    stripped = path.strip("/")
    if method in ["GET", "HEAD"] and stripped:
        # assume that this is an S3 GET request with URL path `/<bucket>/<key ...>`
        return ServiceModelIdentifier("s3")

    # detect S3 URLs
    if stripped and "/" not in stripped:
        if method == "PUT":
            # assume that this is an S3 PUT bucket request with URL path `/<bucket>`
            return ServiceModelIdentifier("s3")
        if method == "POST" and "key" in request.values:
            # assume that this is an S3 POST request with form parameters or multipart form in the body
            return ServiceModelIdentifier("s3")

    # detect S3 requests sent from aws-cli using --no-sign-request option
    if "aws-cli/" in str(request.user_agent):
        return ServiceModelIdentifier("s3")

    # detect S3 pre-signed URLs (v2 and v4)
    values = request.values
    if any(
        value in values
        for value in [
            "AWSAccessKeyId",
            "Signature",
            "X-Amz-Algorithm",
            "X-Amz-Credential",
            "X-Amz-Date",
            "X-Amz-Expires",
            "X-Amz-SignedHeaders",
            "X-Amz-Signature",
        ]
    ):
        return ServiceModelIdentifier("s3")

    # S3 delete object requests
    if method == "POST" and "delete" in values:
        data_bytes = to_bytes(request.data)
        if b"<Delete" in data_bytes and b"<Key>" in data_bytes:
            return ServiceModelIdentifier("s3")

    # Put Object API can have multiple keys
    if stripped.count("/") >= 1 and method == "PUT":
        # assume that this is an S3 PUT bucket object request with URL path `/<bucket>/object`
        # or `/<bucket>/object/object1/+`
        return ServiceModelIdentifier("s3")

    # detect S3 requests with "AWS id:key" Auth headers
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.startswith("AWS "):
        return ServiceModelIdentifier("s3")

    if uses_host_addressing(request.headers):
        # Note: This needs to be the last rule (and therefore is not in the host rules), since it is incredibly greedy
        return ServiceModelIdentifier("s3")