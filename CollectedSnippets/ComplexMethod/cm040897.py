def list_objects(
        self,
        context: RequestContext,
        bucket: BucketName,
        delimiter: Delimiter = None,
        encoding_type: EncodingType = None,
        marker: Marker = None,
        max_keys: MaxKeys = None,
        prefix: Prefix = None,
        request_payer: RequestPayer = None,
        expected_bucket_owner: AccountId = None,
        optional_object_attributes: OptionalObjectAttributesList = None,
        **kwargs,
    ) -> ListObjectsOutput:
        store, s3_bucket = self._get_cross_account_bucket(context, bucket)
        validate_encoding_type(encoding_type)

        common_prefixes = set()
        count = 0
        is_truncated = False
        next_key_marker = None
        max_keys = max_keys or 1000
        prefix = prefix or ""
        delimiter = delimiter or ""
        if encoding_type == EncodingType.url:
            prefix = urlparse.quote(prefix)
            delimiter = urlparse.quote(delimiter)

        s3_objects: list[Object] = []

        all_keys = sorted(s3_bucket.objects.values(), key=lambda r: r.key)
        last_key = all_keys[-1] if all_keys else None

        # sort by key
        for s3_object in all_keys:
            key = urlparse.quote(s3_object.key) if encoding_type else s3_object.key
            # skip all keys that alphabetically come before key_marker
            if marker:
                if key <= marker:
                    continue

            # Filter for keys that start with prefix
            if prefix and not key.startswith(prefix):
                continue

            # see ListObjectsV2 for the logic comments (shared logic here)
            prefix_including_delimiter = None
            if delimiter and delimiter in (key_no_prefix := key.removeprefix(prefix)):
                pre_delimiter, _, _ = key_no_prefix.partition(delimiter)
                prefix_including_delimiter = f"{prefix}{pre_delimiter}{delimiter}"

                if prefix_including_delimiter in common_prefixes or (
                    marker and marker.startswith(prefix_including_delimiter)
                ):
                    continue

            if prefix_including_delimiter:
                common_prefixes.add(prefix_including_delimiter)
            else:
                # TODO: add RestoreStatus if present
                object_data = Object(
                    Key=key,
                    ETag=s3_object.quoted_etag,
                    Owner=s3_bucket.owner,  # TODO: verify reality
                    Size=s3_object.size,
                    LastModified=s3_object.last_modified,
                    StorageClass=s3_object.storage_class,
                )

                if s3_object.checksum_algorithm:
                    object_data["ChecksumAlgorithm"] = [s3_object.checksum_algorithm]
                    object_data["ChecksumType"] = s3_object.checksum_type

                s3_objects.append(object_data)

            # we just added a CommonPrefix or an Object, increase the counter
            count += 1
            if count >= max_keys and last_key.key != s3_object.key:
                is_truncated = True
                if prefix_including_delimiter:
                    next_key_marker = prefix_including_delimiter
                elif s3_objects:
                    next_key_marker = s3_objects[-1]["Key"]
                break

        common_prefixes = [CommonPrefix(Prefix=prefix) for prefix in sorted(common_prefixes)]

        response = ListObjectsOutput(
            IsTruncated=is_truncated,
            Name=bucket,
            MaxKeys=max_keys,
            Prefix=prefix or "",
            Marker=marker or "",
        )
        if s3_objects:
            response["Contents"] = s3_objects
        if encoding_type:
            response["EncodingType"] = EncodingType.url
        if delimiter:
            response["Delimiter"] = delimiter
        if common_prefixes:
            response["CommonPrefixes"] = common_prefixes
        if delimiter and next_key_marker:
            response["NextMarker"] = next_key_marker
        if s3_bucket.bucket_region != "us-east-1":
            response["BucketRegion"] = s3_bucket.bucket_region

        # RequestCharged: Optional[RequestCharged]  # TODO
        return response