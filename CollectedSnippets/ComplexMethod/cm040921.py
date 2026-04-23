def create(
        self,
        request: ResourceRequest[S3BucketProperties],
    ) -> ProgressEvent[S3BucketProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/BucketName


        Create-only properties:
          - /properties/BucketName
          - /properties/ObjectLockEnabled

        Read-only properties:
          - /properties/Arn
          - /properties/DomainName
          - /properties/DualStackDomainName
          - /properties/RegionalDomainName
          - /properties/WebsiteURL

        IAM permissions required:
          - s3:CreateBucket
          - s3:PutBucketTagging
          - s3:PutAnalyticsConfiguration
          - s3:PutEncryptionConfiguration
          - s3:PutBucketCORS
          - s3:PutInventoryConfiguration
          - s3:PutLifecycleConfiguration
          - s3:PutMetricsConfiguration
          - s3:PutBucketNotification
          - s3:PutBucketReplication
          - s3:PutBucketWebsite
          - s3:PutAccelerateConfiguration
          - s3:PutBucketPublicAccessBlock
          - s3:PutReplicationConfiguration
          - s3:PutObjectAcl
          - s3:PutBucketObjectLockConfiguration
          - s3:GetBucketAcl
          - s3:ListBucket
          - iam:PassRole
          - s3:DeleteObject
          - s3:PutBucketLogging
          - s3:PutBucketVersioning
          - s3:PutObjectLockConfiguration
          - s3:PutBucketOwnershipControls
          - s3:PutBucketIntelligentTieringConfiguration

        """
        model = request.desired_state
        s3_client = request.aws_client_factory.s3

        if not model.get("BucketName"):
            model["BucketName"] = util.generate_default_name(
                stack_name=request.stack_name, logical_resource_id=request.logical_resource_id
            )
        model["BucketName"] = normalize_bucket_name(model["BucketName"])

        self._create_bucket_if_does_not_exist(model, request.region_name, s3_client)

        self._setup_post_creation_attributes(model, request.region_name)

        if put_config := self._get_s3_bucket_notification_config(model):
            s3_client.put_bucket_notification_configuration(**put_config)

        if version_conf := model.get("VersioningConfiguration"):
            # from the documentation, it seems that `Status` is a required parameter
            s3_client.put_bucket_versioning(
                Bucket=model["BucketName"],
                VersioningConfiguration={
                    "Status": version_conf.get("Status", "Suspended"),
                },
            )

        if cors_configuration := self._transform_cfn_cors(model.get("CorsConfiguration")):
            s3_client.put_bucket_cors(
                Bucket=model["BucketName"],
                CORSConfiguration=cors_configuration,
            )

        if object_lock_configuration := model.get("ObjectLockConfiguration"):
            s3_client.put_object_lock_configuration(
                Bucket=model["BucketName"],
                ObjectLockConfiguration=object_lock_configuration,
            )

        if tags := model.get("Tags"):
            s3_client.put_bucket_tagging(Bucket=model["BucketName"], Tagging={"TagSet": tags})

        if website_config := self._transform_website_configuration(
            model.get("WebsiteConfiguration")
        ):
            s3_client.put_bucket_website(
                Bucket=model["BucketName"],
                WebsiteConfiguration=website_config,
            )

        return ProgressEvent(
            status=OperationStatus.SUCCESS,
            resource_model=model,
            custom_context=request.custom_context,
        )