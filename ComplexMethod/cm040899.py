def list_object_versions(
        self,
        context: RequestContext,
        bucket: BucketName,
        delimiter: Delimiter = None,
        encoding_type: EncodingType = None,
        key_marker: KeyMarker = None,
        max_keys: MaxKeys = None,
        prefix: Prefix = None,
        version_id_marker: VersionIdMarker = None,
        expected_bucket_owner: AccountId = None,
        request_payer: RequestPayer = None,
        optional_object_attributes: OptionalObjectAttributesList = None,
        **kwargs,
    ) -> ListObjectVersionsOutput:
        if version_id_marker and not key_marker:
            raise InvalidArgument(
                "A version-id marker cannot be specified without a key marker.",
                ArgumentName="version-id-marker",
                ArgumentValue=version_id_marker,
            )
        validate_encoding_type(encoding_type)

        store, s3_bucket = self._get_cross_account_bucket(context, bucket)
        common_prefixes = set()
        count = 0
        is_truncated = False
        next_key_marker = None
        next_version_id_marker = None
        max_keys = max_keys or 1000
        prefix = prefix or ""
        delimiter = delimiter or ""
        if encoding_type == EncodingType.url:
            prefix = urlparse.quote(prefix)
            delimiter = urlparse.quote(delimiter)
        version_key_marker_found = False

        object_versions: list[ObjectVersion] = []
        delete_markers: list[DeleteMarkerEntry] = []

        all_versions = s3_bucket.objects.values(with_versions=True)
        # sort by key, and last-modified-date, to get the last version first
        all_versions.sort(key=lambda r: (r.key, -r.last_modified.timestamp()))
        last_version = all_versions[-1] if all_versions else None

        for version in all_versions:
            key = urlparse.quote(version.key) if encoding_type else version.key
            # skip all keys that alphabetically come before key_marker
            if key_marker:
                if key < key_marker:
                    continue
                elif key == key_marker:
                    if not version_id_marker:
                        continue
                    # as the keys are ordered by time, once we found the key marker, we can return the next one
                    if version.version_id == version_id_marker:
                        version_key_marker_found = True
                        continue

                    # it is possible that the version_id_marker related object has been deleted, in that case, start
                    # as soon as the next version id is older than the version id marker (meaning this version was
                    # next after the now-deleted version)
                    elif is_version_older_than_other(version.version_id, version_id_marker):
                        version_key_marker_found = True

                    elif not version_key_marker_found:
                        # as long as we have not passed the version_key_marker, skip the versions
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
                    key_marker and key_marker.startswith(prefix_including_delimiter)
                ):
                    continue

            if prefix_including_delimiter:
                common_prefixes.add(prefix_including_delimiter)

            elif isinstance(version, S3DeleteMarker):
                delete_marker = DeleteMarkerEntry(
                    Key=key,
                    Owner=s3_bucket.owner,
                    VersionId=version.version_id,
                    IsLatest=version.is_current,
                    LastModified=version.last_modified,
                )
                delete_markers.append(delete_marker)
            else:
                # TODO: add RestoreStatus if present
                object_version = ObjectVersion(
                    Key=key,
                    ETag=version.quoted_etag,
                    Owner=s3_bucket.owner,  # TODO: verify reality
                    Size=version.size,
                    VersionId=version.version_id or "null",
                    LastModified=version.last_modified,
                    IsLatest=version.is_current,
                    # TODO: verify this, are other class possible?
                    # StorageClass=version.storage_class,
                    StorageClass=ObjectVersionStorageClass.STANDARD,
                )

                if version.checksum_algorithm:
                    object_version["ChecksumAlgorithm"] = [version.checksum_algorithm]
                    object_version["ChecksumType"] = version.checksum_type

                object_versions.append(object_version)

            # we just added a CommonPrefix, an Object or a DeleteMarker, increase the counter
            count += 1
            if count >= max_keys and last_version.version_id != version.version_id:
                is_truncated = True
                if prefix_including_delimiter:
                    next_key_marker = prefix_including_delimiter
                else:
                    next_key_marker = version.key
                    next_version_id_marker = version.version_id
                break

        common_prefixes = [CommonPrefix(Prefix=prefix) for prefix in sorted(common_prefixes)]

        response = ListObjectVersionsOutput(
            IsTruncated=is_truncated,
            Name=bucket,
            MaxKeys=max_keys,
            Prefix=prefix,
            KeyMarker=key_marker or "",
            VersionIdMarker=version_id_marker or "",
        )
        if object_versions:
            response["Versions"] = object_versions
        if encoding_type:
            response["EncodingType"] = EncodingType.url
        if delete_markers:
            response["DeleteMarkers"] = delete_markers
        if delimiter:
            response["Delimiter"] = delimiter
        if common_prefixes:
            response["CommonPrefixes"] = common_prefixes
        if next_key_marker:
            response["NextKeyMarker"] = next_key_marker
        if next_version_id_marker:
            response["NextVersionIdMarker"] = next_version_id_marker

        # RequestCharged: Optional[RequestCharged]  # TODO
        return response