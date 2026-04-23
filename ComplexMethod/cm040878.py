def validate_inventory_configuration(
    config_id: InventoryId, inventory_configuration: InventoryConfiguration
):
    """
    Validate the Inventory Configuration following AWS docs
    Validation order is XML then `Id` then S3DestinationBucket
    https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutBucketInventoryConfiguration.html
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
    :param config_id: the passed Id parameter passed to the provider method
    :param inventory_configuration: InventoryConfiguration
    :raises MalformedXML: when the file doesn't follow the basic structure/required fields
    :raises IdMismatch: if the `Id` parameter is different from the `Id` field from the configuration
    :raises InvalidS3DestinationBucket: if S3 bucket is not provided as an ARN
    :return: None
    """
    required_root_fields = {"Destination", "Id", "IncludedObjectVersions", "IsEnabled", "Schedule"}
    optional_root_fields = {"Filter", "OptionalFields"}

    if not validate_dict_fields(
        inventory_configuration, required_root_fields, optional_root_fields
    ):
        raise MalformedXML()

    required_s3_bucket_dest_fields = {"Bucket", "Format"}
    optional_s3_bucket_dest_fields = {"AccountId", "Encryption", "Prefix"}

    if not (
        s3_bucket_destination := inventory_configuration["Destination"].get("S3BucketDestination")
    ) or not validate_dict_fields(
        s3_bucket_destination, required_s3_bucket_dest_fields, optional_s3_bucket_dest_fields
    ):
        raise MalformedXML()

    if inventory_configuration["Destination"]["S3BucketDestination"]["Format"] not in (
        "CSV",
        "ORC",
        "Parquet",
    ):
        raise MalformedXML()

    if not (frequency := inventory_configuration["Schedule"].get("Frequency")) or frequency not in (
        "Daily",
        "Weekly",
    ):
        raise MalformedXML()

    if inventory_configuration["IncludedObjectVersions"] not in ("All", "Current"):
        raise MalformedXML()

    possible_optional_fields = {
        "Size",
        "LastModifiedDate",
        "StorageClass",
        "ETag",
        "IsMultipartUploaded",
        "ReplicationStatus",
        "EncryptionStatus",
        "ObjectLockRetainUntilDate",
        "ObjectLockMode",
        "ObjectLockLegalHoldStatus",
        "IntelligentTieringAccessTier",
        "BucketKeyStatus",
        "ChecksumAlgorithm",
    }
    if (opt_fields := inventory_configuration.get("OptionalFields")) and set(
        opt_fields
    ) - possible_optional_fields:
        raise MalformedXML()

    if inventory_configuration.get("Id") != config_id:
        raise CommonServiceException(
            code="IdMismatch", message="Document ID does not match the specified configuration ID."
        )

    bucket_arn = inventory_configuration["Destination"]["S3BucketDestination"]["Bucket"]
    try:
        arns.parse_arn(bucket_arn)
    except InvalidArnException:
        raise CommonServiceException(
            code="InvalidS3DestinationBucket", message="Invalid bucket ARN."
        )