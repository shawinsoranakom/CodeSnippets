def complete_multipart_upload(
        self,
        context: RequestContext,
        bucket: BucketName,
        key: ObjectKey,
        upload_id: MultipartUploadId,
        multipart_upload: CompletedMultipartUpload = None,
        checksum_crc32: ChecksumCRC32 = None,
        checksum_crc32_c: ChecksumCRC32C = None,
        checksum_crc64_nvme: ChecksumCRC64NVME = None,
        checksum_sha1: ChecksumSHA1 = None,
        checksum_sha256: ChecksumSHA256 = None,
        checksum_type: ChecksumType = None,
        mpu_object_size: MpuObjectSize = None,
        request_payer: RequestPayer = None,
        expected_bucket_owner: AccountId = None,
        if_match: IfMatch = None,
        if_none_match: IfNoneMatch = None,
        sse_customer_algorithm: SSECustomerAlgorithm = None,
        sse_customer_key: SSECustomerKey = None,
        sse_customer_key_md5: SSECustomerKeyMD5 = None,
        **kwargs,
    ) -> CompleteMultipartUploadOutput:
        store, s3_bucket = self._get_cross_account_bucket(context, bucket)

        if (
            not (s3_multipart := s3_bucket.multiparts.get(upload_id))
            or s3_multipart.object.key != key
        ):
            raise NoSuchUpload(
                "The specified upload does not exist. The upload ID may be invalid, or the upload may have been aborted or completed.",
                UploadId=upload_id,
            )

        if if_none_match and if_match:
            raise NotImplementedException(
                "A header you provided implies functionality that is not implemented",
                Header="If-Match,If-None-Match",
                additionalMessage="Multiple conditional request headers present in the request",
            )

        elif if_none_match:
            # TODO: improve concurrency mechanism for `if_none_match` and `if_match`
            if if_none_match != "*":
                raise NotImplementedException(
                    "A header you provided implies functionality that is not implemented",
                    Header="If-None-Match",
                    additionalMessage="We don't accept the provided value of If-None-Match header for this API",
                )
            if object_exists_for_precondition_write(s3_bucket, key):
                raise PreconditionFailed(
                    "At least one of the pre-conditions you specified did not hold",
                    Condition="If-None-Match",
                )
            elif s3_multipart.precondition:
                raise ConditionalRequestConflict(
                    "The conditional request cannot succeed due to a conflicting operation against this resource.",
                    Condition="If-None-Match",
                    Key=key,
                )

        elif if_match:
            if if_match == "*":
                raise NotImplementedException(
                    "A header you provided implies functionality that is not implemented",
                    Header="If-None-Match",
                    additionalMessage="We don't accept the provided value of If-None-Match header for this API",
                )
            verify_object_equality_precondition_write(
                s3_bucket, key, if_match, initiated=s3_multipart.initiated
            )

        parts = multipart_upload.get("Parts", [])
        if not parts:
            raise InvalidRequest("You must specify at least one part")

        parts_numbers = [part.get("PartNumber") for part in parts]
        # TODO: it seems that with new S3 data integrity, sorting might not be mandatory depending on checksum type
        # see https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html
        # sorted is very fast (fastest) if the list is already sorted, which should be the case
        if sorted(parts_numbers) != parts_numbers:
            raise InvalidPartOrder(
                "The list of parts was not in ascending order. Parts must be ordered by part number.",
                UploadId=upload_id,
            )

        mpu_checksum_algorithm = s3_multipart.checksum_algorithm
        mpu_checksum_type = s3_multipart.checksum_type

        if checksum_type and checksum_type != mpu_checksum_type:
            raise InvalidRequest(
                f"The upload was created using the {mpu_checksum_type or 'null'} checksum mode. "
                f"The complete request must use the same checksum mode."
            )

        # generate the versionId before completing, in case the bucket versioning status has changed between
        # creation and completion? AWS validate this
        version_id = generate_version_id(s3_bucket.versioning_status)
        s3_multipart.object.version_id = version_id

        # we're inspecting the signature of `complete_multipart`, in case the multipart has been restored from
        # persistence. if we do not have a new version, do not validate those parameters
        # TODO: remove for next major version (minor?)
        if signature(s3_multipart.complete_multipart).parameters.get("mpu_size"):
            checksum_algorithm = mpu_checksum_algorithm.lower() if mpu_checksum_algorithm else None
            checksum_map = {
                "crc32": checksum_crc32,
                "crc32c": checksum_crc32_c,
                "crc64nvme": checksum_crc64_nvme,
                "sha1": checksum_sha1,
                "sha256": checksum_sha256,
            }
            checksum_value = checksum_map.get(checksum_algorithm)
            s3_multipart.complete_multipart(
                parts, mpu_size=mpu_object_size, validation_checksum=checksum_value
            )
            if mpu_checksum_algorithm and (
                (
                    checksum_value
                    and mpu_checksum_type == ChecksumType.FULL_OBJECT
                    and not checksum_type
                )
                or any(
                    checksum_value
                    for checksum_type, checksum_value in checksum_map.items()
                    if checksum_type != checksum_algorithm
                )
            ):
                # this is not ideal, but this validation comes last... after the validation of individual parts
                s3_multipart.object.parts.clear()
                raise BadDigest(
                    f"The {mpu_checksum_algorithm.lower()} you specified did not match the calculated checksum."
                )
        else:
            s3_multipart.complete_multipart(parts)

        stored_multipart = self._storage_backend.get_multipart(bucket, s3_multipart)
        stored_multipart.complete_multipart(
            [s3_multipart.parts.get(str(part_number)) for part_number in parts_numbers]
        )
        if not s3_multipart.checksum_algorithm and s3_multipart.object.checksum_algorithm:
            with self._storage_backend.open(
                bucket, s3_multipart.object, mode="r"
            ) as s3_stored_object:
                s3_multipart.object.checksum_value = s3_stored_object.checksum
                s3_multipart.object.checksum_type = ChecksumType.FULL_OBJECT

        s3_object = s3_multipart.object

        s3_bucket.objects.set(key, s3_object)

        # remove the multipart now that it's complete
        self._storage_backend.remove_multipart(bucket, s3_multipart)
        s3_bucket.multiparts.pop(s3_multipart.id, None)

        key_id = get_unique_key_id(bucket, key, version_id)
        store.tags.delete_all_tags(key_id)
        if s3_multipart.tagging:
            store.tags.update_tags(key_id, s3_multipart.tagging)

        # RequestCharged: Optional[RequestCharged] TODO

        response = CompleteMultipartUploadOutput(
            Bucket=bucket,
            Key=key,
            ETag=s3_object.quoted_etag,
            Location=get_url_encoded_object_location(bucket, key),
        )

        if s3_object.version_id:
            response["VersionId"] = s3_object.version_id

        # it seems AWS is not returning checksum related fields if the object has KMS encryption ¯\_(ツ)_/¯
        # but it still generates them, and they can be retrieved with regular GetObject and such operations
        if s3_object.checksum_algorithm and not s3_object.kms_key_id:
            response[f"Checksum{s3_object.checksum_algorithm.upper()}"] = s3_object.checksum_value
            response["ChecksumType"] = s3_object.checksum_type

        if s3_object.expiration:
            response["Expiration"] = s3_object.expiration  # TODO: properly parse the datetime

        add_encryption_to_response(response, s3_object=s3_object)

        self._notify(context, s3_bucket=s3_bucket, s3_object=s3_object)

        return response