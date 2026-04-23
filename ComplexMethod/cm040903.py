def upload_part_copy(
        self,
        context: RequestContext,
        request: UploadPartCopyRequest,
    ) -> UploadPartCopyOutput:
        # TODO: handle following parameters:
        #  SSECustomerAlgorithm: Optional[SSECustomerAlgorithm]
        #  SSECustomerKey: Optional[SSECustomerKey]
        #  SSECustomerKeyMD5: Optional[SSECustomerKeyMD5]
        #  CopySourceSSECustomerAlgorithm: Optional[CopySourceSSECustomerAlgorithm]
        #  CopySourceSSECustomerKey: Optional[CopySourceSSECustomerKey]
        #  CopySourceSSECustomerKeyMD5: Optional[CopySourceSSECustomerKeyMD5]
        #  RequestPayer: Optional[RequestPayer]
        #  ExpectedBucketOwner: Optional[AccountId]
        #  ExpectedSourceBucketOwner: Optional[AccountId]
        dest_bucket = request["Bucket"]
        dest_key = request["Key"]
        store = self.get_store(context.account_id, context.region)
        # TODO: validate cross-account UploadPartCopy
        if not (dest_s3_bucket := store.buckets.get(dest_bucket)):
            raise NoSuchBucket("The specified bucket does not exist", BucketName=dest_bucket)

        src_bucket, src_key, src_version_id = extract_bucket_key_version_id_from_copy_source(
            request.get("CopySource")
        )

        if not (src_s3_bucket := store.buckets.get(src_bucket)):
            raise NoSuchBucket("The specified bucket does not exist", BucketName=src_bucket)

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

        upload_id = request.get("UploadId")
        if (
            not (s3_multipart := dest_s3_bucket.multiparts.get(upload_id))
            or s3_multipart.object.key != dest_key
        ):
            raise NoSuchUpload(
                "The specified upload does not exist. "
                "The upload ID may be invalid, or the upload may have been aborted or completed.",
                UploadId=upload_id,
            )

        elif (part_number := request.get("PartNumber", 0)) < 1 or part_number > 10000:
            raise InvalidArgument(
                "Part number must be an integer between 1 and 10000, inclusive",
                ArgumentName="partNumber",
                ArgumentValue=part_number,
            )

        source_range = request.get("CopySourceRange")
        # TODO implement copy source IF

        range_data: ObjectRange | None = None
        if source_range:
            range_data = parse_copy_source_range_header(source_range, src_s3_object.size)

        if precondition := get_failed_upload_part_copy_source_preconditions(
            request, src_s3_object.last_modified, src_s3_object.etag
        ):
            raise PreconditionFailed(
                "At least one of the pre-conditions you specified did not hold",
                Condition=precondition,
            )

        s3_part = S3Part(part_number=part_number)
        if s3_multipart.checksum_algorithm:
            s3_part.checksum_algorithm = s3_multipart.checksum_algorithm

        stored_multipart = self._storage_backend.get_multipart(dest_bucket, s3_multipart)
        stored_multipart.copy_from_object(s3_part, src_bucket, src_s3_object, range_data)

        s3_multipart.parts[str(part_number)] = s3_part

        # TODO: return those fields
        #     RequestCharged: Optional[RequestCharged]

        result = CopyPartResult(
            ETag=s3_part.quoted_etag,
            LastModified=s3_part.last_modified,
        )

        response = UploadPartCopyOutput(
            CopyPartResult=result,
        )

        if src_s3_bucket.versioning_status and src_s3_object.version_id:
            response["CopySourceVersionId"] = src_s3_object.version_id

        if s3_part.checksum_algorithm:
            result[f"Checksum{s3_part.checksum_algorithm.upper()}"] = s3_part.checksum_value

        add_encryption_to_response(response, s3_object=s3_multipart.object)

        return response