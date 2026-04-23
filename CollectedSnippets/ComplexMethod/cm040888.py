def _get_cross_account_bucket(
        self,
        context: RequestContext,
        bucket_name: BucketName,
        *,
        expected_bucket_owner: AccountId = None,
    ) -> tuple[S3Store, S3Bucket]:
        if expected_bucket_owner and not re.fullmatch(r"\w{12}", expected_bucket_owner):
            raise InvalidBucketOwnerAWSAccountID(
                f"The value of the expected bucket owner parameter must be an AWS Account ID... [{expected_bucket_owner}]",
            )

        request_store = self.get_store(context.account_id, context.region)
        if not (s3_bucket := request_store.buckets.get(bucket_name)):
            if not (bucket_account_id := request_store.global_bucket_map.get(bucket_name)):
                raise NoSuchBucket("The specified bucket does not exist", BucketName=bucket_name)

            bucket_account_store = self.get_store(bucket_account_id, context.region)
            if not (s3_bucket := bucket_account_store.buckets.get(bucket_name)):
                raise NoSuchBucket("The specified bucket does not exist", BucketName=bucket_name)

        if expected_bucket_owner and s3_bucket.bucket_account_id != expected_bucket_owner:
            raise AccessDenied("Access Denied")

        regional_bucket_store = self.get_store(s3_bucket.bucket_account_id, s3_bucket.bucket_region)
        return regional_bucket_store, s3_bucket