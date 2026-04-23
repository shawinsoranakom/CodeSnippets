def put_object_lock_configuration(
        self,
        context: RequestContext,
        bucket: BucketName,
        object_lock_configuration: ObjectLockConfiguration = None,
        request_payer: RequestPayer = None,
        token: ObjectLockToken = None,
        content_md5: ContentMD5 = None,
        checksum_algorithm: ChecksumAlgorithm = None,
        expected_bucket_owner: AccountId = None,
        **kwargs,
    ) -> PutObjectLockConfigurationOutput:
        store, s3_bucket = self._get_cross_account_bucket(context, bucket)
        if s3_bucket.versioning_status != "Enabled":
            raise InvalidBucketState(
                "Versioning must be 'Enabled' on the bucket to apply a Object Lock configuration"
            )

        if (
            not object_lock_configuration
            or object_lock_configuration.get("ObjectLockEnabled") != "Enabled"
        ):
            raise MalformedXML()

        if "Rule" not in object_lock_configuration:
            s3_bucket.object_lock_default_retention = None
            if not s3_bucket.object_lock_enabled:
                s3_bucket.object_lock_enabled = True

            return PutObjectLockConfigurationOutput()
        elif not (rule := object_lock_configuration["Rule"]) or not (
            default_retention := rule.get("DefaultRetention")
        ):
            raise MalformedXML()

        if "Mode" not in default_retention or (
            ("Days" in default_retention and "Years" in default_retention)
            or ("Days" not in default_retention and "Years" not in default_retention)
        ):
            raise MalformedXML()

        if default_retention["Mode"] not in OBJECT_LOCK_MODES:
            raise MalformedXML()

        s3_bucket.object_lock_default_retention = default_retention
        if not s3_bucket.object_lock_enabled:
            s3_bucket.object_lock_enabled = True

        return PutObjectLockConfigurationOutput()