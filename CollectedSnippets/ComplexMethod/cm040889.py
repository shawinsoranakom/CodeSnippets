def create_bucket(
        self,
        context: RequestContext,
        request: CreateBucketRequest,
    ) -> CreateBucketOutput:
        if context.region == "aws-global":
            # TODO: extend this logic to probably all the provider, and maybe all services. S3 is the most impacted
            #  right now so this will help users to properly set a region in their config
            # See the `TestS3.test_create_bucket_aws_global` test
            raise AuthorizationHeaderMalformed(
                f"The authorization header is malformed; the region 'aws-global' is wrong; expecting '{AWS_REGION_US_EAST_1}'",
                HostId=S3_HOST_ID,
                Region=AWS_REGION_US_EAST_1,
            )

        bucket_name = request["Bucket"]

        if not is_bucket_name_valid(bucket_name):
            raise InvalidBucketName("The specified bucket is not valid.", BucketName=bucket_name)

        create_bucket_configuration = request.get("CreateBucketConfiguration") or {}

        bucket_tags = create_bucket_configuration.get("Tags", [])
        if bucket_tags:
            validate_tag_set(bucket_tags, type_set="create-bucket")

        location_constraint = create_bucket_configuration.get("LocationConstraint", "")
        validate_location_constraint(context.region, location_constraint)

        bucket_region = location_constraint
        if not location_constraint:
            bucket_region = AWS_REGION_US_EAST_1
        if location_constraint == BucketLocationConstraint.EU:
            bucket_region = AWS_REGION_EU_WEST_1

        store = self.get_store(context.account_id, bucket_region)

        if bucket_name in store.global_bucket_map:
            existing_bucket_owner = store.global_bucket_map[bucket_name]
            if existing_bucket_owner != context.account_id:
                raise BucketAlreadyExists()

            # if the existing bucket has the same owner, the behaviour will depend on the region and if the request has
            # tags
            if bucket_region != AWS_REGION_US_EAST_1 or bucket_tags:
                raise BucketAlreadyOwnedByYou(
                    "Your previous request to create the named bucket succeeded and you already own it.",
                    BucketName=bucket_name,
                )
            else:
                existing_bucket = store.buckets[bucket_name]
                # CreateBucket is idempotent in us-east-1
                return CreateBucketOutput(
                    Location=f"/{bucket_name}",
                    BucketArn=existing_bucket.bucket_arn,
                )

        if (
            object_ownership := request.get("ObjectOwnership")
        ) is not None and object_ownership not in OBJECT_OWNERSHIPS:
            raise InvalidArgument(
                f"Invalid x-amz-object-ownership header: {object_ownership}",
                ArgumentName="x-amz-object-ownership",
            )
        # see https://docs.aws.amazon.com/AmazonS3/latest/API/API_Owner.html
        owner = get_owner_for_account_id(context.account_id)
        acl = get_access_control_policy_for_new_resource_request(request, owner=owner)

        s3_bucket = S3Bucket(
            name=bucket_name,
            account_id=context.account_id,
            bucket_region=bucket_region,
            owner=owner,
            acl=acl,
            object_ownership=request.get("ObjectOwnership"),
            object_lock_enabled_for_bucket=request.get("ObjectLockEnabledForBucket") or False,
            location_constraint=location_constraint,
        )

        store.buckets[bucket_name] = s3_bucket
        store.global_bucket_map[bucket_name] = s3_bucket.bucket_account_id
        if bucket_tags:
            store.tags.update_tags(
                s3_bucket.bucket_arn, {tag["Key"]: tag["Value"] for tag in bucket_tags}
            )
        self._cors_handler.invalidate_cache()
        self._storage_backend.create_bucket(bucket_name)

        # Location is always contained in response -> full url for LocationConstraint outside us-east-1
        location = (
            f"/{bucket_name}"
            if bucket_region == "us-east-1"
            else get_full_default_bucket_location(bucket_name)
        )
        response = CreateBucketOutput(Location=location, BucketArn=s3_bucket.bucket_arn)
        return response