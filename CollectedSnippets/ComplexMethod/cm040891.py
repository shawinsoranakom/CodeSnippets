def put_object(
        self,
        context: RequestContext,
        request: PutObjectRequest,
    ) -> PutObjectOutput:
        # TODO: validate order of validation
        # TODO: still need to handle following parameters
        #  request_payer: RequestPayer = None,
        bucket_name = request["Bucket"]
        key = request["Key"]
        store, s3_bucket = self._get_cross_account_bucket(context, bucket_name)

        if (storage_class := request.get("StorageClass")) is not None and (
            storage_class not in STORAGE_CLASSES or storage_class == StorageClass.OUTPOSTS
        ):
            raise InvalidStorageClass(
                "The storage class you specified is not valid", StorageClassRequested=storage_class
            )

        if not config.S3_SKIP_KMS_KEY_VALIDATION and (sse_kms_key_id := request.get("SSEKMSKeyId")):
            validate_kms_key_id(sse_kms_key_id, s3_bucket)

        validate_object_key(key)

        if_match = request.get("IfMatch")
        if (if_none_match := request.get("IfNoneMatch")) and if_match:
            raise NotImplementedException(
                "A header you provided implies functionality that is not implemented",
                Header="If-Match,If-None-Match",
                additionalMessage="Multiple conditional request headers present in the request",
            )

        elif (if_none_match and if_none_match != "*") or (if_match and if_match == "*"):
            header_name = "If-None-Match" if if_none_match else "If-Match"
            raise NotImplementedException(
                "A header you provided implies functionality that is not implemented",
                Header=header_name,
                additionalMessage=f"We don't accept the provided value of {header_name} header for this API",
            )

        system_metadata = get_system_metadata_from_request(request)
        if not system_metadata.get("ContentType"):
            system_metadata["ContentType"] = "binary/octet-stream"

        user_metadata = decode_user_metadata(request.get("Metadata"))

        version_id = generate_version_id(s3_bucket.versioning_status)
        if version_id != "null":
            # if we are in a versioned bucket, we need to lock around the full key (all the versions)
            # because object versions have locks per version
            precondition_lock = self._preconditions_locks[bucket_name][key]
        else:
            precondition_lock = contextlib.nullcontext()

        etag_content_md5 = ""
        if content_md5 := request.get("ContentMD5"):
            # assert that the received ContentMD5 is a properly b64 encoded value that fits a MD5 hash length
            etag_content_md5 = base_64_content_md5_to_etag(content_md5)
            if not etag_content_md5:
                raise InvalidDigest(
                    "The Content-MD5 you specified was invalid.",
                    Content_MD5=content_md5,
                )

        checksum_algorithm = get_s3_checksum_algorithm_from_request(request)
        checksum_value = (
            request.get(f"Checksum{checksum_algorithm.upper()}") if checksum_algorithm else None
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

        if tagging := request.get("Tagging"):
            tagging = parse_tagging_header(tagging)

        s3_object = S3Object(
            key=key,
            version_id=version_id,
            storage_class=storage_class,
            expires=request.get("Expires"),
            user_metadata=user_metadata,
            system_metadata=system_metadata,
            checksum_algorithm=checksum_algorithm,
            checksum_value=checksum_value,
            encryption=encryption_parameters.encryption,
            kms_key_id=encryption_parameters.kms_key_id,
            bucket_key_enabled=encryption_parameters.bucket_key_enabled,
            sse_key_hash=sse_c_key_md5,
            lock_mode=lock_parameters.lock_mode,
            lock_legal_status=lock_parameters.lock_legal_status,
            lock_until=lock_parameters.lock_until,
            website_redirect_location=request.get("WebsiteRedirectLocation"),
            acl=acl,
            owner=s3_bucket.owner,  # TODO: for now we only have one owner, but it can depends on Bucket settings
        )

        body = request.get("Body")
        # check if chunked request
        headers = context.request.headers
        is_aws_chunked = headers.get("x-amz-content-sha256", "").startswith(
            "STREAMING-"
        ) or "aws-chunked" in headers.get("content-encoding", "")
        if is_aws_chunked:
            checksum_algorithm = (
                checksum_algorithm
                or get_s3_checksum_algorithm_from_trailing_headers(headers.get("x-amz-trailer", ""))
            )
            if checksum_algorithm:
                s3_object.checksum_algorithm = checksum_algorithm

            decoded_content_length = int(headers.get("x-amz-decoded-content-length", 0))
            body = AwsChunkedDecoder(body, decoded_content_length, s3_object=s3_object)

            # S3 removes the `aws-chunked` value from ContentEncoding
            if content_encoding := s3_object.system_metadata.pop("ContentEncoding", None):
                encodings = [enc for enc in content_encoding.split(",") if enc != "aws-chunked"]
                if encodings:
                    s3_object.system_metadata["ContentEncoding"] = ",".join(encodings)

        with (
            precondition_lock,
            self._storage_backend.open(bucket_name, s3_object, mode="w") as s3_stored_object,
        ):
            # as we are inside the lock here, if multiple concurrent requests happen for the same object, it's the first
            # one to finish to succeed, and subsequent will raise exceptions. Once the first write finishes, we're
            # opening the lock and other requests can check this condition
            if if_none_match and object_exists_for_precondition_write(s3_bucket, key):
                raise PreconditionFailed(
                    "At least one of the pre-conditions you specified did not hold",
                    Condition="If-None-Match",
                )

            elif if_match:
                verify_object_equality_precondition_write(s3_bucket, key, if_match)

            s3_stored_object.write(body)

            if s3_object.checksum_algorithm:
                if not s3_object.checksum_value:
                    s3_object.checksum_value = s3_stored_object.checksum
                elif not validate_checksum_value(s3_object.checksum_value, checksum_algorithm):
                    self._storage_backend.remove(bucket_name, s3_object)
                    raise InvalidRequest(
                        f"Value for x-amz-checksum-{s3_object.checksum_algorithm.lower()} header is invalid."
                    )
                elif s3_object.checksum_value != s3_stored_object.checksum:
                    self._storage_backend.remove(bucket_name, s3_object)
                    raise BadDigest(
                        f"The {checksum_algorithm.upper()} you specified did not match the calculated checksum."
                    )

            # TODO: handle ContentMD5 and ChecksumAlgorithm in a handler for all requests except requests with a
            #  streaming body. We can use the specs to verify which operations needs to have the checksum validated
            if content_md5:
                calculated_md5 = etag_to_base_64_content_md5(s3_stored_object.etag)
                if calculated_md5 != content_md5:
                    self._storage_backend.remove(bucket_name, s3_object)
                    raise BadDigest(
                        "The Content-MD5 you specified did not match what we received.",
                        ExpectedDigest=etag_content_md5,
                        CalculatedDigest=calculated_md5,
                    )

            s3_bucket.objects.set(key, s3_object)

        # in case we are overriding an object, delete the tags entry
        key_id = get_unique_key_id(bucket_name, key, version_id)
        store.tags.delete_all_tags(key_id)
        if tagging:
            store.tags.update_tags(key_id, tagging)

        # RequestCharged: Optional[RequestCharged]  # TODO
        response = PutObjectOutput(
            ETag=s3_object.quoted_etag,
        )
        if s3_bucket.versioning_status == "Enabled":
            response["VersionId"] = s3_object.version_id

        if s3_object.checksum_algorithm:
            response[f"Checksum{s3_object.checksum_algorithm}"] = s3_object.checksum_value
            response["ChecksumType"] = s3_object.checksum_type

        if s3_bucket.lifecycle_rules:
            if expiration_header := self._get_expiration_header(
                s3_bucket.lifecycle_rules,
                bucket_name,
                s3_object,
                store.tags.get_tags(key_id),
            ):
                # TODO: we either apply the lifecycle to existing objects when we set the new rules, or we need to
                #  apply them everytime we get/head an object
                response["Expiration"] = expiration_header

        add_encryption_to_response(response, s3_object=s3_object)
        if sse_c_key_md5:
            response["SSECustomerAlgorithm"] = "AES256"
            response["SSECustomerKeyMD5"] = sse_c_key_md5

        self._notify(context, s3_bucket=s3_bucket, s3_object=s3_object)

        return response