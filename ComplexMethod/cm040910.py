def post_object(
        self, context: RequestContext, bucket: BucketName, body: IO[Body] = None, **kwargs
    ) -> PostResponse:
        if "multipart/form-data" not in context.request.headers.get("Content-Type", ""):
            raise PreconditionFailed(
                "At least one of the pre-conditions you specified did not hold",
                Condition="Bucket POST must be of the enclosure-type multipart/form-data",
            )
        # see https://docs.aws.amazon.com/AmazonS3/latest/API/RESTObjectPOST.html
        # TODO: signature validation is not implemented for pre-signed POST
        # policy validation is not implemented either, except expiration and mandatory fields
        # This operation is the only one using form for storing the request data. We will have to do some manual
        # parsing here, as no specs are present for this, as no client directly implements this operation.
        store, s3_bucket = self._get_cross_account_bucket(context, bucket)

        form = context.request.form
        object_key = context.request.form.get("key")

        if "file" in form:
            # in AWS, you can pass the file content as a string in the form field and not as a file object
            file_data = to_bytes(form["file"])
            object_content_length = len(file_data)
            stream = BytesIO(file_data)
        else:
            # this is the default behaviour
            fileobj = context.request.files["file"]
            stream = fileobj.stream
            # stream is a SpooledTemporaryFile, so we can seek the stream to know its length, necessary for policy
            # validation
            original_pos = stream.tell()
            object_content_length = stream.seek(0, 2)
            # reset the stream and put it back at its original position
            stream.seek(original_pos, 0)

            if "${filename}" in object_key:
                # TODO: ${filename} is actually usable in all form fields
                # See https://docs.aws.amazon.com/sdk-for-ruby/v3/api/Aws/S3/PresignedPost.html
                # > The string ${filename} is automatically replaced with the name of the file provided by the user and
                # is recognized by all form fields.
                object_key = object_key.replace("${filename}", fileobj.filename)

        # TODO: see if we need to pass additional metadata not contained in the policy from the table under
        # https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-HTTPPOSTConstructPolicy.html#sigv4-PolicyConditions
        additional_policy_metadata = {
            "bucket": bucket,
            "content_length": object_content_length,
        }
        validate_post_policy(form, additional_policy_metadata)

        if canned_acl := form.get("acl"):
            validate_canned_acl(canned_acl)
            acp = get_canned_acl(canned_acl, owner=s3_bucket.owner)
        else:
            acp = get_canned_acl(BucketCannedACL.private, owner=s3_bucket.owner)

        post_system_settable_headers = [
            "Cache-Control",
            "Content-Type",
            "Content-Disposition",
            "Content-Encoding",
        ]
        system_metadata = {}
        for system_metadata_field in post_system_settable_headers:
            if field_value := form.get(system_metadata_field):
                system_key = system_metadata_field.replace("-", "")
                system_metadata[system_key] = field_value

        if not system_metadata.get("ContentType"):
            system_metadata["ContentType"] = "binary/octet-stream"

        user_metadata = {
            field.removeprefix("x-amz-meta-").lower(): form.get(field)
            for field in form
            if field.startswith("x-amz-meta-")
        }

        if tagging := form.get("tagging"):
            # this is weird, as it's direct XML in the form, we need to parse it directly
            tagging = parse_post_object_tagging_xml(tagging)

        if (storage_class := form.get("x-amz-storage-class")) is not None and (
            storage_class not in STORAGE_CLASSES or storage_class == StorageClass.OUTPOSTS
        ):
            raise InvalidStorageClass(
                "The storage class you specified is not valid", StorageClassRequested=storage_class
            )

        encryption_request = {
            "ServerSideEncryption": form.get("x-amz-server-side-encryption"),
            "SSEKMSKeyId": form.get("x-amz-server-side-encryption-aws-kms-key-id"),
            "BucketKeyEnabled": form.get("x-amz-server-side-encryption-bucket-key-enabled"),
        }

        encryption_parameters = get_encryption_parameters_from_request_and_bucket(
            encryption_request,
            s3_bucket,
            store,
        )

        checksum_algorithm = form.get("x-amz-checksum-algorithm")
        checksum_value = (
            form.get(f"x-amz-checksum-{checksum_algorithm.lower()}") if checksum_algorithm else None
        )
        expires = (
            str_to_rfc_1123_datetime(expires_str) if (expires_str := form.get("Expires")) else None
        )

        version_id = generate_version_id(s3_bucket.versioning_status)

        s3_object = S3Object(
            key=object_key,
            version_id=version_id,
            storage_class=storage_class,
            expires=expires,
            user_metadata=user_metadata,
            system_metadata=system_metadata,
            checksum_algorithm=checksum_algorithm,
            checksum_value=checksum_value,
            encryption=encryption_parameters.encryption,
            kms_key_id=encryption_parameters.kms_key_id,
            bucket_key_enabled=encryption_parameters.bucket_key_enabled,
            website_redirect_location=form.get("x-amz-website-redirect-location"),
            acl=acp,
            owner=s3_bucket.owner,  # TODO: for now we only have one owner, but it can depends on Bucket settings
        )

        with self._storage_backend.open(bucket, s3_object, mode="w") as s3_stored_object:
            s3_stored_object.write(stream)

            if not s3_object.checksum_value:
                s3_object.checksum_value = s3_stored_object.checksum

            elif checksum_algorithm and s3_object.checksum_value != s3_stored_object.checksum:
                self._storage_backend.remove(bucket, s3_object)
                raise InvalidRequest(
                    f"Value for x-amz-checksum-{checksum_algorithm.lower()} header is invalid."
                )

            s3_bucket.objects.set(object_key, s3_object)

        # in case we are overriding an object, delete the tags entry
        key_id = get_unique_key_id(bucket, object_key, version_id)
        store.tags.delete_all_tags(key_id)
        if tagging:
            store.tags.update_tags(key_id, tagging)

        response = PostResponse()
        # hacky way to set the etag in the headers as well: two locations for one value
        response["ETagHeader"] = s3_object.quoted_etag

        if redirect := form.get("success_action_redirect"):
            # we need to create the redirect, as the parser could not return the moto-calculated one
            try:
                redirect = create_redirect_for_post_request(
                    base_redirect=redirect,
                    bucket=bucket,
                    object_key=object_key,
                    etag=s3_object.quoted_etag,
                )
                response["LocationHeader"] = redirect
                response["StatusCode"] = 303
            except ValueError:
                # If S3 cannot interpret the URL, it acts as if the field is not present.
                response["StatusCode"] = form.get("success_action_status", 204)

        elif status_code := form.get("success_action_status"):
            response["StatusCode"] = status_code
        else:
            response["StatusCode"] = 204

        response["LocationHeader"] = response.get(
            "LocationHeader",
            get_url_encoded_object_location(bucket, object_key),
        )

        if s3_bucket.versioning_status == "Enabled":
            response["VersionId"] = s3_object.version_id

        if s3_object.checksum_algorithm:
            response[f"Checksum{s3_object.checksum_algorithm.upper()}"] = s3_object.checksum_value
            response["ChecksumType"] = ChecksumType.FULL_OBJECT

        if s3_bucket.lifecycle_rules:
            if expiration_header := self._get_expiration_header(
                s3_bucket.lifecycle_rules,
                bucket,
                s3_object,
                store.tags.get_tags(key_id),
            ):
                # TODO: we either apply the lifecycle to existing objects when we set the new rules, or we need to
                #  apply them everytime we get/head an object
                response["Expiration"] = expiration_header

        add_encryption_to_response(response, s3_object=s3_object)

        self._notify(context, s3_bucket=s3_bucket, s3_object=s3_object)

        if response["StatusCode"] == "201":
            # if the StatusCode is 201, S3 returns an XML body with additional information
            response["ETag"] = s3_object.quoted_etag
            response["Bucket"] = bucket
            response["Key"] = object_key
            response["Location"] = response["LocationHeader"]

        return response