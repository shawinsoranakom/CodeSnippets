def head_object(
        self,
        context: RequestContext,
        request: HeadObjectRequest,
    ) -> HeadObjectOutput:
        bucket_name = request["Bucket"]
        object_key = request["Key"]
        version_id = request.get("VersionId")
        store, s3_bucket = self._get_cross_account_bucket(context, bucket_name)

        s3_object = s3_bucket.get_object(
            key=object_key,
            version_id=version_id,
            http_method="HEAD",
        )

        validate_failed_precondition(request, s3_object.last_modified, s3_object.etag)

        sse_c_key_md5 = request.get("SSECustomerKeyMD5")
        if s3_object.sse_key_hash:
            if not sse_c_key_md5:
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

        response = HeadObjectOutput(
            AcceptRanges="bytes",
            **s3_object.get_system_metadata_fields(),
        )
        if s3_object.user_metadata:
            response["Metadata"] = encode_user_metadata(s3_object.user_metadata)

        checksum_value = None
        checksum_type = None
        if checksum_algorithm := s3_object.checksum_algorithm:
            if (request.get("ChecksumMode") or "").upper() == "ENABLED":
                checksum_value = s3_object.checksum_value
                checksum_type = s3_object.checksum_type

        if s3_object.parts and request.get("PartNumber"):
            response["PartsCount"] = len(s3_object.parts)

        if s3_object.version_id:
            response["VersionId"] = s3_object.version_id

        if s3_object.website_redirect_location:
            response["WebsiteRedirectLocation"] = s3_object.website_redirect_location

        if s3_object.restore:
            response["Restore"] = s3_object.restore

        range_header = request.get("Range")
        part_number = request.get("PartNumber")
        if range_header and part_number:
            raise InvalidRequest("Cannot specify both Range header and partNumber query parameter")
        range_data = None
        if range_header:
            range_data = parse_range_header(range_header, s3_object.size)
        elif part_number:
            range_data = get_part_range(s3_object, part_number)

        if range_data:
            response["ContentLength"] = range_data.content_length
            response["ContentRange"] = range_data.content_range
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
        elif checksum_value:
            response[f"Checksum{checksum_algorithm.upper()}"] = checksum_value
            response["ChecksumType"] = checksum_type

        add_encryption_to_response(response, s3_object=s3_object)
        object_tags = store.tags.get_tags(
            get_unique_key_id(bucket_name, object_key, s3_object.version_id)
        )
        if tag_count := len(object_tags):
            response["TagCount"] = tag_count

        # if you specify the VersionId, AWS won't return the Expiration header, even if that's the current version
        if not version_id and s3_bucket.lifecycle_rules:
            if expiration_header := self._get_expiration_header(
                s3_bucket.lifecycle_rules,
                bucket_name,
                s3_object,
                object_tags,
            ):
                # TODO: we either apply the lifecycle to existing objects when we set the new rules, or we need to
                #  apply them everytime we get/head an object
                response["Expiration"] = expiration_header

        if s3_object.lock_mode:
            response["ObjectLockMode"] = s3_object.lock_mode
            if s3_object.lock_until:
                response["ObjectLockRetainUntilDate"] = s3_object.lock_until
        if s3_object.lock_legal_status:
            response["ObjectLockLegalHoldStatus"] = s3_object.lock_legal_status

        if sse_c_key_md5:
            response["SSECustomerAlgorithm"] = "AES256"
            response["SSECustomerKeyMD5"] = sse_c_key_md5

        # TODO: missing return fields:
        #  ArchiveStatus: Optional[ArchiveStatus]
        #  RequestCharged: Optional[RequestCharged]
        #  ReplicationStatus: Optional[ReplicationStatus]

        return response