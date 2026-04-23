def put_object_retention(
        self,
        context: RequestContext,
        bucket: BucketName,
        key: ObjectKey,
        retention: ObjectLockRetention = None,
        request_payer: RequestPayer = None,
        version_id: ObjectVersionId = None,
        bypass_governance_retention: BypassGovernanceRetention = None,
        content_md5: ContentMD5 = None,
        checksum_algorithm: ChecksumAlgorithm = None,
        expected_bucket_owner: AccountId = None,
        **kwargs,
    ) -> PutObjectRetentionOutput:
        store, s3_bucket = self._get_cross_account_bucket(context, bucket)
        if not s3_bucket.object_lock_enabled:
            raise InvalidRequest("Bucket is missing Object Lock Configuration")

        s3_object = s3_bucket.get_object(
            key=key,
            version_id=version_id,
            http_method="PUT",
        )

        if retention and (
            not validate_dict_fields(retention, required_fields={"Mode", "RetainUntilDate"})
            or retention["Mode"] not in OBJECT_LOCK_MODES
        ):
            raise MalformedXML()

        if retention and retention["RetainUntilDate"] < datetime.datetime.now(datetime.UTC):
            # weirdly, this date is format as following: Tue Dec 31 16:00:00 PST 2019
            # it contains the timezone as PST, even if you target a bucket in Europe or Asia
            pst_datetime = retention["RetainUntilDate"].astimezone(
                tz=ZoneInfo("America/Los_Angeles")
            )
            raise InvalidArgument(
                "The retain until date must be in the future!",
                ArgumentName="RetainUntilDate",
                ArgumentValue=pst_datetime.strftime("%a %b %d %H:%M:%S %Z %Y"),
            )

        is_request_reducing_locking = (
            not retention
            or (s3_object.lock_until and s3_object.lock_until > retention["RetainUntilDate"])
            or (
                retention["Mode"] == ObjectLockMode.GOVERNANCE
                and s3_object.lock_mode == ObjectLockMode.COMPLIANCE
            )
        )
        if is_request_reducing_locking and (
            s3_object.lock_mode == ObjectLockMode.COMPLIANCE
            or (
                s3_object.lock_mode == ObjectLockMode.GOVERNANCE and not bypass_governance_retention
            )
        ):
            raise AccessDenied("Access Denied because object protected by object lock.")

        s3_object.lock_mode = retention["Mode"] if retention else None
        s3_object.lock_until = retention["RetainUntilDate"] if retention else None

        # TODO: return RequestCharged
        return PutObjectRetentionOutput()