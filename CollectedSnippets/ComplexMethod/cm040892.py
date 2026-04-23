def get_object(
        self,
        context: RequestContext,
        request: GetObjectRequest,
    ) -> GetObjectOutput:
        # TODO: missing handling parameters:
        #  request_payer: RequestPayer = None,
        #  expected_bucket_owner: AccountId = None,

        bucket_name = request["Bucket"]
        object_key = request["Key"]
        version_id = request.get("VersionId")
        store, s3_bucket = self._get_cross_account_bucket(context, bucket_name)

        s3_object = s3_bucket.get_object(
            key=object_key,
            version_id=version_id,
            http_method="GET",
        )

        if s3_object.storage_class in ARCHIVES_STORAGE_CLASSES and not s3_object.restore:
            raise InvalidObjectState(
                "The operation is not valid for the object's storage class",
                StorageClass=s3_object.storage_class,
            )

        if not config.S3_SKIP_KMS_KEY_VALIDATION and s3_object.kms_key_id:
            validate_kms_key_id(kms_key=s3_object.kms_key_id, bucket=s3_bucket)

        sse_c_key_md5 = request.get("SSECustomerKeyMD5")
        if s3_object.sse_key_hash:
            if s3_object.sse_key_hash and not sse_c_key_md5:
                raise InvalidRequest(
                    "The object was stored using a form of Server Side Encryption. "
                    "The correct parameters must be provided to retrieve the object."
                )
            elif s3_object.sse_key_hash != sse_c_key_md5:
                raise AccessDenied(
                    "Requests specifying Server Side Encryption with Customer provided keys must provide the correct secret key."
                )

        validate_sse_c(
            algorithm=request.get("SSECustomerAlgorithm"),
            encryption_key=request.get("SSECustomerKey"),
            encryption_key_md5=sse_c_key_md5,
        )

        validate_failed_precondition(request, s3_object.last_modified, s3_object.etag)

        range_header = request.get("Range")
        part_number = request.get("PartNumber")
        if range_header and part_number:
            raise InvalidRequest("Cannot specify both Range header and partNumber query parameter")
        range_data = None
        if range_header:
            range_data = parse_range_header(range_header, s3_object.size)
        elif part_number:
            range_data = get_part_range(s3_object, part_number)

        # we deliberately do not call `.close()` on the s3_stored_object to keep the read lock acquired. When passing
        # the object to Werkzeug, the handler will call `.close()` after finishing iterating over `__iter__`.
        # this can however lead to deadlocks if an exception happens between the call and returning the object.
        # Be careful into adding validation between this call and `return` of `S3Provider.get_object`
        s3_stored_object = self._storage_backend.open(bucket_name, s3_object, mode="r")

        # this is a hacky way to verify the object hasn't been modified between `s3_object = s3_bucket.get_object`
        # and the storage backend call. If it has been modified, now that we're in the read lock, we can safely fetch
        # the object again
        if s3_stored_object.last_modified != s3_object.internal_last_modified:
            s3_object = s3_bucket.get_object(
                key=object_key,
                version_id=version_id,
                http_method="GET",
            )

        response = GetObjectOutput(
            AcceptRanges="bytes",
            **s3_object.get_system_metadata_fields(),
        )
        if s3_object.user_metadata:
            response["Metadata"] = encode_user_metadata(s3_object.user_metadata)

        if s3_object.parts and request.get("PartNumber"):
            response["PartsCount"] = len(s3_object.parts)

        if s3_object.version_id:
            response["VersionId"] = s3_object.version_id

        if s3_object.website_redirect_location:
            response["WebsiteRedirectLocation"] = s3_object.website_redirect_location

        if s3_object.restore:
            response["Restore"] = s3_object.restore

        checksum_value = None
        checksum_type = None
        if checksum_algorithm := s3_object.checksum_algorithm:
            if (request.get("ChecksumMode") or "").upper() == "ENABLED":
                checksum_value = s3_object.checksum_value
                checksum_type = s3_object.checksum_type

        if range_data:
            s3_stored_object.seek(range_data.begin)
            response["Body"] = LimitedIterableStream(
                s3_stored_object, max_length=range_data.content_length
            )
            response["ContentRange"] = range_data.content_range
            response["ContentLength"] = range_data.content_length
            response["StatusCode"] = 206
            if checksum_value:
                if s3_object.parts and part_number and checksum_type == ChecksumType.COMPOSITE:
                    part_data = s3_object.parts[str(part_number)]
                    checksum_key = f"Checksum{checksum_algorithm.upper()}"
                    response[checksum_key] = part_data.get(checksum_key)
                    response["ChecksumType"] = ChecksumType.COMPOSITE

                # it means either the range header means the whole object, or that a multipart upload with `FULL_OBJECT`
                # only had one part
                elif range_data.content_length == s3_object.size:
                    response[f"Checksum{checksum_algorithm.upper()}"] = checksum_value
                    response["ChecksumType"] = checksum_type
        else:
            response["Body"] = s3_stored_object
            if checksum_value:
                response[f"Checksum{checksum_algorithm.upper()}"] = checksum_value
                response["ChecksumType"] = checksum_type

        add_encryption_to_response(response, s3_object=s3_object)

        object_tags = store.tags.get_tags(get_unique_key_id(bucket_name, object_key, version_id))

        if tag_count := len(object_tags):
            response["TagCount"] = tag_count
        if s3_object.is_current and s3_bucket.lifecycle_rules:
            if expiration_header := self._get_expiration_header(
                s3_bucket.lifecycle_rules,
                bucket_name,
                s3_object,
                object_tags,
            ):
                # TODO: we either apply the lifecycle to existing objects when we set the new rules, or we need to
                #  apply them everytime we get/head an object
                response["Expiration"] = expiration_header

        # TODO: missing returned fields
        #     RequestCharged: Optional[RequestCharged]
        #     ReplicationStatus: Optional[ReplicationStatus]

        if s3_object.lock_mode:
            response["ObjectLockMode"] = s3_object.lock_mode
            if s3_object.lock_until:
                response["ObjectLockRetainUntilDate"] = s3_object.lock_until
        if s3_object.lock_legal_status:
            response["ObjectLockLegalHoldStatus"] = s3_object.lock_legal_status

        if sse_c_key_md5:
            response["SSECustomerAlgorithm"] = "AES256"
            response["SSECustomerKeyMD5"] = sse_c_key_md5

        for request_param, response_param in ALLOWED_HEADER_OVERRIDES.items():
            if request_param_value := request.get(request_param):
                if isinstance(request_param_value, str):
                    try:
                        request_param_value.encode("latin-1")
                    except UnicodeEncodeError:
                        raise InvalidArgument(
                            "Header value cannot be represented using ISO-8859-1.",
                            ArgumentName=header_name_from_capitalized_param(request_param),
                            ArgumentValue=request_param_value,
                            HostId=S3_HOST_ID,
                        )

                response[response_param] = request_param_value

        return response