def put_bucket_encryption(
        self,
        context: RequestContext,
        bucket: BucketName,
        server_side_encryption_configuration: ServerSideEncryptionConfiguration,
        content_md5: ContentMD5 = None,
        checksum_algorithm: ChecksumAlgorithm = None,
        expected_bucket_owner: AccountId = None,
        **kwargs,
    ) -> None:
        store, s3_bucket = self._get_cross_account_bucket(context, bucket)

        if not (rules := server_side_encryption_configuration.get("Rules")):
            raise MalformedXML()

        if len(rules) != 1 or not (
            encryption := rules[0].get("ApplyServerSideEncryptionByDefault")
        ):
            raise MalformedXML()

        if not (sse_algorithm := encryption.get("SSEAlgorithm")):
            raise MalformedXML()

        if sse_algorithm not in SSE_ALGORITHMS:
            raise MalformedXML()

        if sse_algorithm != ServerSideEncryption.aws_kms and "KMSMasterKeyID" in encryption:
            raise InvalidArgument(
                "a KMSMasterKeyID is not applicable if the default sse algorithm is not aws:kms or aws:kms:dsse",
                ArgumentName="ApplyServerSideEncryptionByDefault",
            )
        # elif master_kms_key := encryption.get("KMSMasterKeyID"):
        # TODO: validate KMS key? not currently done in moto
        # You can pass either the KeyId or the KeyArn. If cross-account, it has to be the ARN.
        # It's always saved as the ARN in the bucket configuration.
        # kms_key_arn = get_kms_key_arn(master_kms_key, s3_bucket.bucket_account_id)
        # encryption["KMSMasterKeyID"] = master_kms_key

        s3_bucket.encryption_rule = rules[0]