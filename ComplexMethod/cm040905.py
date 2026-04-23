def list_parts(
        self,
        context: RequestContext,
        bucket: BucketName,
        key: ObjectKey,
        upload_id: MultipartUploadId,
        max_parts: MaxParts = None,
        part_number_marker: PartNumberMarker = None,
        request_payer: RequestPayer = None,
        expected_bucket_owner: AccountId = None,
        sse_customer_algorithm: SSECustomerAlgorithm = None,
        sse_customer_key: SSECustomerKey = None,
        sse_customer_key_md5: SSECustomerKeyMD5 = None,
        **kwargs,
    ) -> ListPartsOutput:
        store, s3_bucket = self._get_cross_account_bucket(context, bucket)

        if (
            not (s3_multipart := s3_bucket.multiparts.get(upload_id))
            or s3_multipart.object.key != key
        ):
            raise NoSuchUpload(
                "The specified upload does not exist. "
                "The upload ID may be invalid, or the upload may have been aborted or completed.",
                UploadId=upload_id,
            )

        count = 0
        is_truncated = False
        part_number_marker = part_number_marker or 0
        max_parts = max_parts or 1000

        parts = []
        all_parts = sorted(
            (int(part_number), part) for part_number, part in s3_multipart.parts.items()
        )
        last_part_number = all_parts[-1][0] if all_parts else None
        for part_number, part in all_parts:
            if part_number <= part_number_marker:
                continue
            part_item = Part(
                ETag=part.quoted_etag,
                LastModified=part.last_modified,
                PartNumber=part_number,
                Size=part.size,
            )
            if s3_multipart.checksum_algorithm and part.checksum_algorithm:
                part_item[f"Checksum{part.checksum_algorithm.upper()}"] = part.checksum_value

            parts.append(part_item)
            count += 1

            if count >= max_parts and part.part_number != last_part_number:
                is_truncated = True
                break

        response = ListPartsOutput(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            Initiator=s3_multipart.initiator,
            Owner=s3_multipart.object.owner,
            StorageClass=s3_multipart.object.storage_class,
            IsTruncated=is_truncated,
            MaxParts=max_parts,
            PartNumberMarker=0,
            NextPartNumberMarker=0,
        )
        if parts:
            response["Parts"] = parts
            last_part = parts[-1]["PartNumber"]
            response["NextPartNumberMarker"] = last_part

        if part_number_marker:
            response["PartNumberMarker"] = part_number_marker
        if s3_multipart.checksum_algorithm:
            response["ChecksumAlgorithm"] = s3_multipart.object.checksum_algorithm
            response["ChecksumType"] = s3_multipart.checksum_type

        #     AbortDate: Optional[AbortDate] TODO: lifecycle
        #     AbortRuleId: Optional[AbortRuleId] TODO: lifecycle
        #     RequestCharged: Optional[RequestCharged]

        return response