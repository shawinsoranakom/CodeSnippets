def get_object_lock_parameters_from_bucket_and_request(
    request: PutObjectRequest | CopyObjectRequest | CreateMultipartUploadRequest,
    s3_bucket: S3Bucket,
):
    lock_mode = request.get("ObjectLockMode")
    lock_legal_status = request.get("ObjectLockLegalHoldStatus")
    lock_until = request.get("ObjectLockRetainUntilDate")

    if lock_mode and not lock_until:
        raise InvalidArgument(
            "x-amz-object-lock-retain-until-date and x-amz-object-lock-mode must both be supplied",
            ArgumentName="x-amz-object-lock-retain-until-date",
        )
    elif not lock_mode and lock_until:
        raise InvalidArgument(
            "x-amz-object-lock-retain-until-date and x-amz-object-lock-mode must both be supplied",
            ArgumentName="x-amz-object-lock-mode",
        )

    if lock_mode and lock_mode not in OBJECT_LOCK_MODES:
        raise InvalidArgument(
            "Unknown wormMode directive.",
            ArgumentName="x-amz-object-lock-mode",
            ArgumentValue=lock_mode,
        )

    if (default_retention := s3_bucket.object_lock_default_retention) and not lock_mode:
        lock_mode = default_retention["Mode"]
        lock_until = get_retention_from_now(
            days=default_retention.get("Days"),
            years=default_retention.get("Years"),
        )

    return ObjectLockParameters(lock_until, lock_legal_status, lock_mode)