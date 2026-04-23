def get_object_attributes(
        self,
        context: RequestContext,
        request: GetObjectAttributesRequest,
    ) -> GetObjectAttributesOutput:
        bucket_name = request["Bucket"]
        object_key = request["Key"]
        store, s3_bucket = self._get_cross_account_bucket(context, bucket_name)

        s3_object = s3_bucket.get_object(
            key=object_key,
            version_id=request.get("VersionId"),
            http_method="GET",
        )

        sse_c_key_md5 = request.get("SSECustomerKeyMD5")
        if s3_object.sse_key_hash:
            if not sse_c_key_md5:
                raise InvalidRequest(
                    "The object was stored using a form of Server Side Encryption. "
                    "The correct parameters must be provided to retrieve the object."
                )
            elif s3_object.sse_key_hash != sse_c_key_md5:
                raise AccessDenied("Access Denied")

        validate_sse_c(
            algorithm=request.get("SSECustomerAlgorithm"),
            encryption_key=request.get("SSECustomerKey"),
            encryption_key_md5=sse_c_key_md5,
        )

        object_attrs = request.get("ObjectAttributes", [])
        response = GetObjectAttributesOutput()
        object_checksum_type = s3_object.checksum_type
        if "ETag" in object_attrs:
            response["ETag"] = s3_object.etag
        if "StorageClass" in object_attrs:
            response["StorageClass"] = s3_object.storage_class
        if "ObjectSize" in object_attrs:
            response["ObjectSize"] = s3_object.size
        if "Checksum" in object_attrs and (checksum_algorithm := s3_object.checksum_algorithm):
            if s3_object.parts:
                checksum_value = s3_object.checksum_value.split("-")[0]
            else:
                checksum_value = s3_object.checksum_value
            response["Checksum"] = {
                f"Checksum{checksum_algorithm.upper()}": checksum_value,
                "ChecksumType": object_checksum_type,
            }

        response["LastModified"] = s3_object.last_modified

        if s3_bucket.versioning_status:
            response["VersionId"] = s3_object.version_id

        if "ObjectParts" in object_attrs and s3_object.parts:
            if object_checksum_type == ChecksumType.FULL_OBJECT:
                response["ObjectParts"] = GetObjectAttributesParts(
                    TotalPartsCount=len(s3_object.parts)
                )
            else:
                # this is basically a simplified `ListParts` call on the object, only returned when the checksum type is
                # COMPOSITE
                count = 0
                is_truncated = False
                part_number_marker = request.get("PartNumberMarker") or 0
                max_parts = request.get("MaxParts") or 1000

                parts = []
                all_parts = sorted(
                    (int(part_number), part) for part_number, part in s3_object.parts.items()
                )
                last_part_number, last_part = all_parts[-1]

                for part_number, part in all_parts:
                    if part_number <= part_number_marker:
                        continue
                    part_item = select_from_typed_dict(ObjectPart, part)

                    parts.append(part_item)
                    count += 1

                    if count >= max_parts and part["PartNumber"] != last_part_number:
                        is_truncated = True
                        break

                object_parts = GetObjectAttributesParts(
                    TotalPartsCount=len(s3_object.parts),
                    IsTruncated=is_truncated,
                    MaxParts=max_parts,
                    PartNumberMarker=part_number_marker,
                    NextPartNumberMarker=0,
                )
                if parts:
                    object_parts["Parts"] = parts
                    object_parts["NextPartNumberMarker"] = parts[-1]["PartNumber"]

                response["ObjectParts"] = object_parts

        return response