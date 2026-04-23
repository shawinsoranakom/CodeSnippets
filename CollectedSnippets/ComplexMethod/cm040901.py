def create_multipart_upload(
        self,
        context: RequestContext,
        request: CreateMultipartUploadRequest,
    ) -> CreateMultipartUploadOutput:
        # TODO: handle missing parameters:
        #  request_payer: RequestPayer = None,
        bucket_name = request["Bucket"]
        store, s3_bucket = self._get_cross_account_bucket(context, bucket_name)

        if (storage_class := request.get("StorageClass")) is not None and (
            storage_class not in STORAGE_CLASSES or storage_class == StorageClass.OUTPOSTS
        ):
            raise InvalidStorageClass(
                "The storage class you specified is not valid", StorageClassRequested=storage_class
            )

        if not config.S3_SKIP_KMS_KEY_VALIDATION and (sse_kms_key_id := request.get("SSEKMSKeyId")):
            validate_kms_key_id(sse_kms_key_id, s3_bucket)

        if tagging := request.get("Tagging"):
            tagging = parse_tagging_header(tagging_header=tagging)

        key = request["Key"]

        system_metadata = get_system_metadata_from_request(request)
        if not system_metadata.get("ContentType"):
            system_metadata["ContentType"] = "binary/octet-stream"

        user_metadata = decode_user_metadata(request.get("Metadata"))

        checksum_algorithm = request.get("ChecksumAlgorithm")
        if checksum_algorithm and checksum_algorithm not in CHECKSUM_ALGORITHMS:
            raise InvalidRequest(
                "Checksum algorithm provided is unsupported. Please try again with any of the valid types: [CRC32, CRC32C, CRC64NVME, SHA1, SHA256]"
            )

        if not (checksum_type := request.get("ChecksumType")) and checksum_algorithm:
            if checksum_algorithm == ChecksumAlgorithm.CRC64NVME:
                checksum_type = ChecksumType.FULL_OBJECT
            else:
                checksum_type = ChecksumType.COMPOSITE
        elif checksum_type and not checksum_algorithm:
            raise InvalidRequest(
                "The x-amz-checksum-type header can only be used with the x-amz-checksum-algorithm header."
            )

        if (
            checksum_type == ChecksumType.COMPOSITE
            and checksum_algorithm == ChecksumAlgorithm.CRC64NVME
        ):
            raise InvalidRequest(
                "The COMPOSITE checksum type cannot be used with the crc64nvme checksum algorithm."
            )
        elif checksum_type == ChecksumType.FULL_OBJECT and checksum_algorithm.upper().startswith(
            "SHA"
        ):
            raise InvalidRequest(
                f"The FULL_OBJECT checksum type cannot be used with the {checksum_algorithm.lower()} checksum algorithm."
            )

        # TODO: we're not encrypting the object with the provided key for now
        sse_c_key_md5 = request.get("SSECustomerKeyMD5")
        validate_sse_c(
            algorithm=request.get("SSECustomerAlgorithm"),
            encryption_key=request.get("SSECustomerKey"),
            encryption_key_md5=sse_c_key_md5,
            server_side_encryption=request.get("ServerSideEncryption"),
        )

        encryption_parameters = get_encryption_parameters_from_request_and_bucket(
            request,
            s3_bucket,
            store,
        )
        lock_parameters = get_object_lock_parameters_from_bucket_and_request(request, s3_bucket)

        acl = get_access_control_policy_for_new_resource_request(request, owner=s3_bucket.owner)

        initiator = get_owner_for_account_id(context.account_id)
        # This is weird, but for all other operations, AWS does not return a DisplayName anymore except for the
        # `initiator` field in Multipart related operation. We will probably remove this soon once AWS changes that
        initiator["DisplayName"] = "webfile"

        s3_multipart = S3Multipart(
            key=key,
            storage_class=storage_class,
            expires=request.get("Expires"),
            user_metadata=user_metadata,
            system_metadata=system_metadata,
            checksum_algorithm=checksum_algorithm,
            checksum_type=checksum_type,
            encryption=encryption_parameters.encryption,
            kms_key_id=encryption_parameters.kms_key_id,
            bucket_key_enabled=encryption_parameters.bucket_key_enabled,
            sse_key_hash=sse_c_key_md5,
            lock_mode=lock_parameters.lock_mode,
            lock_legal_status=lock_parameters.lock_legal_status,
            lock_until=lock_parameters.lock_until,
            website_redirect_location=request.get("WebsiteRedirectLocation"),
            expiration=None,  # TODO, from lifecycle, or should it be updated with config?
            acl=acl,
            initiator=initiator,
            tagging=tagging,
            owner=s3_bucket.owner,
            precondition=object_exists_for_precondition_write(s3_bucket, key),
        )
        # it seems if there is SSE-C on the multipart, AWS S3 will override the default Checksum behavior (but not on
        # PutObject)
        if sse_c_key_md5:
            s3_multipart.object.checksum_algorithm = None

        s3_bucket.multiparts[s3_multipart.id] = s3_multipart

        response = CreateMultipartUploadOutput(
            Bucket=bucket_name, Key=key, UploadId=s3_multipart.id
        )

        if checksum_algorithm:
            response["ChecksumAlgorithm"] = checksum_algorithm
            response["ChecksumType"] = checksum_type

        add_encryption_to_response(response, s3_object=s3_multipart.object)
        if sse_c_key_md5:
            response["SSECustomerAlgorithm"] = "AES256"
            response["SSECustomerKeyMD5"] = sse_c_key_md5

        # TODO: missing response fields we're not currently supporting
        # - AbortDate: lifecycle related,not currently supported, todo
        # - AbortRuleId: lifecycle related, not currently supported, todo
        # - RequestCharged: todo

        return response