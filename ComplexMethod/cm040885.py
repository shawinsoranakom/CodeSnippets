def get_encryption_parameters_from_request_and_bucket(
    request: PutObjectRequest | CopyObjectRequest | CreateMultipartUploadRequest,
    s3_bucket: S3Bucket,
    store: S3Store,
) -> EncryptionParameters:
    if request.get("SSECustomerKey"):
        # we return early, because ServerSideEncryption does not apply if the request has SSE-C
        return EncryptionParameters(None, None, False)

    encryption = request.get("ServerSideEncryption")
    kms_key_id = request.get("SSEKMSKeyId")
    bucket_key_enabled = request.get("BucketKeyEnabled")
    if s3_bucket.encryption_rule:
        bucket_key_enabled = bucket_key_enabled or s3_bucket.encryption_rule.get("BucketKeyEnabled")
        encryption = (
            encryption
            or s3_bucket.encryption_rule["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
        )
        if encryption == ServerSideEncryption.aws_kms:
            key_id = kms_key_id or s3_bucket.encryption_rule[
                "ApplyServerSideEncryptionByDefault"
            ].get("KMSMasterKeyID")
            kms_key_id = get_kms_key_arn(
                key_id, s3_bucket.bucket_account_id, s3_bucket.bucket_region
            )
            if not kms_key_id:
                # if not key is provided, AWS will use an AWS managed KMS key
                # create it if it doesn't already exist, and save it in the store per region
                if not store.aws_managed_kms_key_id:
                    managed_kms_key_id = create_s3_kms_managed_key_for_region(
                        s3_bucket.bucket_account_id, s3_bucket.bucket_region
                    )
                    store.aws_managed_kms_key_id = managed_kms_key_id

                kms_key_id = store.aws_managed_kms_key_id

    return EncryptionParameters(encryption, kms_key_id, bucket_key_enabled)