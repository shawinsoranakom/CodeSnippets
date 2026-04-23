def copy_object(
        self,
        context: RequestContext,
        request: CopyObjectRequest,
    ) -> CopyObjectOutput:
        # request_payer: RequestPayer = None,  # TODO:
        dest_bucket = request["Bucket"]
        dest_key = request["Key"]

        if_match = request.get("IfMatch")
        if_none_match = request.get("IfNoneMatch")

        if if_none_match and if_match:
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

        validate_object_key(dest_key)
        store, dest_s3_bucket = self._get_cross_account_bucket(context, dest_bucket)

        src_bucket, src_key, src_version_id = extract_bucket_key_version_id_from_copy_source(
            request.get("CopySource")
        )
        _, src_s3_bucket = self._get_cross_account_bucket(context, src_bucket)

        if not config.S3_SKIP_KMS_KEY_VALIDATION and (sse_kms_key_id := request.get("SSEKMSKeyId")):
            validate_kms_key_id(sse_kms_key_id, dest_s3_bucket)

        # if the object is a delete marker, get_object will raise NotFound if no versionId, like AWS
        try:
            src_s3_object = src_s3_bucket.get_object(key=src_key, version_id=src_version_id)
        except MethodNotAllowed:
            raise InvalidRequest(
                "The source of a copy request may not specifically refer to a delete marker by version id."
            )

        if src_s3_object.storage_class in ARCHIVES_STORAGE_CLASSES and not src_s3_object.restore:
            raise InvalidObjectState(
                "Operation is not valid for the source object's storage class",
                StorageClass=src_s3_object.storage_class,
            )

        if failed_condition := get_failed_precondition_copy_source(
            request, src_s3_object.last_modified, src_s3_object.etag
        ):
            raise PreconditionFailed(
                "At least one of the pre-conditions you specified did not hold",
                Condition=failed_condition,
            )

        source_sse_c_key_md5 = request.get("CopySourceSSECustomerKeyMD5")
        if src_s3_object.sse_key_hash:
            if not source_sse_c_key_md5:
                raise InvalidRequest(
                    "The object was stored using a form of Server Side Encryption. "
                    "The correct parameters must be provided to retrieve the object."
                )
            elif src_s3_object.sse_key_hash != source_sse_c_key_md5:
                raise AccessDenied("Access Denied")

        validate_sse_c(
            algorithm=request.get("CopySourceSSECustomerAlgorithm"),
            encryption_key=request.get("CopySourceSSECustomerKey"),
            encryption_key_md5=source_sse_c_key_md5,
        )

        target_sse_c_key_md5 = request.get("SSECustomerKeyMD5")
        server_side_encryption = request.get("ServerSideEncryption")
        # validate target SSE-C parameters
        validate_sse_c(
            algorithm=request.get("SSECustomerAlgorithm"),
            encryption_key=request.get("SSECustomerKey"),
            encryption_key_md5=target_sse_c_key_md5,
            server_side_encryption=server_side_encryption,
        )

        # TODO validate order of validation
        storage_class = request.get("StorageClass")
        metadata_directive = request.get("MetadataDirective")
        website_redirect_location = request.get("WebsiteRedirectLocation")
        # we need to check for identity of the object, to see if the default one has been changed
        is_default_encryption = (
            dest_s3_bucket.encryption_rule is DEFAULT_BUCKET_ENCRYPTION
            and src_s3_object.encryption == "AES256"
        )
        if (
            src_bucket == dest_bucket
            and src_key == dest_key
            and not any(
                (
                    storage_class,
                    server_side_encryption,
                    target_sse_c_key_md5,
                    metadata_directive == "REPLACE",
                    website_redirect_location,
                    dest_s3_bucket.encryption_rule
                    and not is_default_encryption,  # S3 will allow copy in place if the bucket has encryption configured
                    src_s3_object.restore,
                )
            )
        ):
            raise InvalidRequest(
                "This copy request is illegal because it is trying to copy an object to itself without changing the "
                "object's metadata, storage class, website redirect location or encryption attributes."
            )

        if tagging := request.get("Tagging"):
            tagging = parse_tagging_header(tagging)

        if metadata_directive == "REPLACE":
            user_metadata = decode_user_metadata(request.get("Metadata"))
            system_metadata = get_system_metadata_from_request(request)
            if not system_metadata.get("ContentType"):
                system_metadata["ContentType"] = "binary/octet-stream"
        else:
            user_metadata = src_s3_object.user_metadata
            system_metadata = src_s3_object.system_metadata

        dest_version_id = generate_version_id(dest_s3_bucket.versioning_status)
        if dest_version_id != "null":
            # if we are in a versioned bucket, we need to lock around the full key (all the versions)
            # because object versions have locks per version
            precondition_lock = self._preconditions_locks[dest_bucket][dest_key]
        else:
            precondition_lock = contextlib.nullcontext()

        encryption_parameters = get_encryption_parameters_from_request_and_bucket(
            request,
            dest_s3_bucket,
            store,
        )
        lock_parameters = get_object_lock_parameters_from_bucket_and_request(
            request, dest_s3_bucket
        )

        acl = get_access_control_policy_for_new_resource_request(
            request, owner=dest_s3_bucket.owner
        )
        checksum_algorithm = request.get("ChecksumAlgorithm")

        s3_object = S3Object(
            key=dest_key,
            size=src_s3_object.size,
            version_id=dest_version_id,
            storage_class=storage_class,
            expires=request.get("Expires"),
            user_metadata=user_metadata,
            system_metadata=system_metadata,
            checksum_algorithm=checksum_algorithm or src_s3_object.checksum_algorithm,
            encryption=encryption_parameters.encryption,
            kms_key_id=encryption_parameters.kms_key_id,
            bucket_key_enabled=request.get(
                "BucketKeyEnabled"
            ),  # CopyObject does not inherit from the bucket here
            sse_key_hash=target_sse_c_key_md5,
            lock_mode=lock_parameters.lock_mode,
            lock_legal_status=lock_parameters.lock_legal_status,
            lock_until=lock_parameters.lock_until,
            website_redirect_location=website_redirect_location,
            expiration=None,  # TODO, from lifecycle
            acl=acl,
            owner=dest_s3_bucket.owner,
        )

        with (
            precondition_lock,
            self._storage_backend.copy(
                src_bucket=src_bucket,
                src_object=src_s3_object,
                dest_bucket=dest_bucket,
                dest_object=s3_object,
            ) as s3_stored_object,
        ):
            # Check destination write preconditions inside the lock to prevent race conditions.
            if if_none_match and object_exists_for_precondition_write(dest_s3_bucket, dest_key):
                raise PreconditionFailed(
                    "At least one of the pre-conditions you specified did not hold",
                    Condition="If-None-Match",
                )

            elif if_match:
                verify_object_equality_precondition_write(dest_s3_bucket, dest_key, if_match)

            s3_object.checksum_value = s3_stored_object.checksum or src_s3_object.checksum_value
            s3_object.etag = s3_stored_object.etag or src_s3_object.etag

            dest_s3_bucket.objects.set(dest_key, s3_object)

        dest_key_id = get_unique_key_id(dest_bucket, dest_key, dest_version_id)

        if (request.get("TaggingDirective")) == "REPLACE":
            store.tags.delete_all_tags(dest_key_id)
            store.tags.update_tags(dest_key_id, tagging or {})
        else:
            src_key_id = get_unique_key_id(src_bucket, src_key, src_s3_object.version_id)
            src_tags = store.tags.get_tags(src_key_id)
            store.tags.delete_all_tags(dest_key_id)
            store.tags.update_tags(dest_key_id, src_tags)

        copy_object_result = CopyObjectResult(
            ETag=s3_object.quoted_etag,
            LastModified=s3_object.last_modified,
        )
        if s3_object.checksum_algorithm:
            copy_object_result[f"Checksum{s3_object.checksum_algorithm.upper()}"] = (
                s3_object.checksum_value
            )
            copy_object_result["ChecksumType"] = s3_object.checksum_type

        response = CopyObjectOutput(
            CopyObjectResult=copy_object_result,
        )

        if s3_object.version_id:
            response["VersionId"] = s3_object.version_id

        if s3_object.expiration:
            response["Expiration"] = s3_object.expiration  # TODO: properly parse the datetime

        add_encryption_to_response(response, s3_object=s3_object)
        if target_sse_c_key_md5:
            response["SSECustomerAlgorithm"] = "AES256"
            response["SSECustomerKeyMD5"] = target_sse_c_key_md5

        if (
            src_s3_bucket.versioning_status
            and src_s3_object.version_id
            and src_s3_object.version_id != "null"
        ):
            response["CopySourceVersionId"] = src_s3_object.version_id

        # RequestCharged: Optional[RequestCharged] # TODO
        self._notify(context, s3_bucket=dest_s3_bucket, s3_object=s3_object)

        return response