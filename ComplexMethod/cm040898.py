def list_objects_v2(
        self,
        context: RequestContext,
        bucket: BucketName,
        delimiter: Delimiter = None,
        encoding_type: EncodingType = None,
        max_keys: MaxKeys = None,
        prefix: Prefix = None,
        continuation_token: Token = None,
        fetch_owner: FetchOwner = None,
        start_after: StartAfter = None,
        request_payer: RequestPayer = None,
        expected_bucket_owner: AccountId = None,
        optional_object_attributes: OptionalObjectAttributesList = None,
        **kwargs,
    ) -> ListObjectsV2Output:
        store, s3_bucket = self._get_cross_account_bucket(context, bucket)

        if continuation_token == "":
            raise InvalidArgument(
                "The continuation token provided is incorrect",
                ArgumentName="continuation-token",
            )
        validate_encoding_type(encoding_type)

        common_prefixes = set()
        count = 0
        is_truncated = False
        next_continuation_token = None
        max_keys = max_keys or 1000
        prefix = prefix or ""
        delimiter = delimiter or ""
        start_after = start_after or ""
        decoded_continuation_token = decode_continuation_token(continuation_token)

        if encoding_type == EncodingType.url:
            prefix = urlparse.quote(prefix)
            delimiter = urlparse.quote(delimiter)
            start_after = urlparse.quote(start_after)
            decoded_continuation_token = urlparse.quote(decoded_continuation_token)

        s3_objects: list[Object] = []

        # sort by key
        for s3_object in sorted(s3_bucket.objects.values(), key=lambda r: r.key):
            key = urlparse.quote(s3_object.key) if encoding_type else s3_object.key

            # skip all keys that alphabetically come before continuation_token
            if continuation_token:
                if key < decoded_continuation_token:
                    continue

            elif start_after:
                if key <= start_after:
                    continue

            # Filter for keys that start with prefix
            if prefix and not key.startswith(prefix):
                continue

            # separate keys that contain the same string between the prefix and the first occurrence of the delimiter
            prefix_including_delimiter = None
            if delimiter and delimiter in (key_no_prefix := key.removeprefix(prefix)):
                pre_delimiter, _, _ = key_no_prefix.partition(delimiter)
                prefix_including_delimiter = f"{prefix}{pre_delimiter}{delimiter}"

                # if the CommonPrefix is already in the CommonPrefixes, it doesn't count towards MaxKey, we can skip
                # the entry without increasing the counter. We need to iterate over all of these entries before
                # returning the next continuation marker, to properly start at the next key after this CommonPrefix
                if prefix_including_delimiter in common_prefixes:
                    continue

            # After skipping all entries, verify we're not over the MaxKeys before adding a new entry
            if count >= max_keys:
                is_truncated = True
                next_continuation_token = encode_continuation_token(s3_object.key)
                break

            # if we found a new CommonPrefix, add it to the CommonPrefixes
            # else, it means it's a new Object, add it to the Contents
            if prefix_including_delimiter:
                common_prefixes.add(prefix_including_delimiter)
            else:
                # TODO: add RestoreStatus if present
                object_data = Object(
                    Key=key,
                    ETag=s3_object.quoted_etag,
                    Size=s3_object.size,
                    LastModified=s3_object.last_modified,
                    StorageClass=s3_object.storage_class,
                )

                if fetch_owner:
                    object_data["Owner"] = s3_bucket.owner

                if s3_object.checksum_algorithm:
                    object_data["ChecksumAlgorithm"] = [s3_object.checksum_algorithm]
                    object_data["ChecksumType"] = s3_object.checksum_type

                s3_objects.append(object_data)

            # we just added either a CommonPrefix or an Object to the List, increase the counter by one
            count += 1

        common_prefixes = [CommonPrefix(Prefix=prefix) for prefix in sorted(common_prefixes)]

        response = ListObjectsV2Output(
            IsTruncated=is_truncated,
            Name=bucket,
            MaxKeys=max_keys,
            Prefix=prefix or "",
            KeyCount=count,
        )
        if s3_objects:
            response["Contents"] = s3_objects
        if encoding_type:
            response["EncodingType"] = EncodingType.url
        if delimiter:
            response["Delimiter"] = delimiter
        if common_prefixes:
            response["CommonPrefixes"] = common_prefixes
        if next_continuation_token:
            response["NextContinuationToken"] = next_continuation_token

        if continuation_token:
            response["ContinuationToken"] = continuation_token
        elif start_after:
            response["StartAfter"] = start_after

        if s3_bucket.bucket_region != "us-east-1":
            response["BucketRegion"] = s3_bucket.bucket_region

        # RequestCharged: Optional[RequestCharged]  # TODO
        return response