def list_buckets(
        self,
        context: RequestContext,
        max_buckets: MaxBuckets = None,
        continuation_token: Token = None,
        prefix: Prefix = None,
        bucket_region: BucketRegion = None,
        **kwargs,
    ) -> ListBucketsOutput:
        if bucket_region and not config.ALLOW_NONSTANDARD_REGIONS:
            if bucket_region not in get_valid_regions_for_service(self.service):
                raise InvalidArgument(
                    f"Argument value {bucket_region} is not a valid AWS Region",
                    ArgumentName="bucket-region",
                )

        owner = get_owner_for_account_id(context.account_id)
        store = self.get_store(context.account_id, context.region)

        decoded_continuation_token = (
            to_str(base64.urlsafe_b64decode(continuation_token.encode()))
            if continuation_token
            else None
        )

        count = 0
        buckets: list[Bucket] = []
        next_continuation_token = None

        # Comparing strings with case sensitivity since AWS is case-sensitive
        for bucket in sorted(store.buckets.values(), key=lambda r: r.name):
            if continuation_token and bucket.name < decoded_continuation_token:
                continue

            if prefix and not bucket.name.startswith(prefix):
                continue

            if bucket_region and not bucket.bucket_region == bucket_region:
                continue

            if max_buckets and count >= max_buckets:
                next_continuation_token = to_str(base64.urlsafe_b64encode(bucket.name.encode()))
                break

            output_bucket = Bucket(
                Name=bucket.name,
                CreationDate=bucket.creation_date,
                BucketRegion=bucket.bucket_region,
                BucketArn=bucket.bucket_arn,
            )
            buckets.append(output_bucket)
            count += 1

        return ListBucketsOutput(
            Owner=owner, Buckets=buckets, Prefix=prefix, ContinuationToken=next_continuation_token
        )