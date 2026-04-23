def list_multipart_uploads(
        self,
        context: RequestContext,
        bucket: BucketName,
        delimiter: Delimiter = None,
        encoding_type: EncodingType = None,
        key_marker: KeyMarker = None,
        max_uploads: MaxUploads = None,
        prefix: Prefix = None,
        upload_id_marker: UploadIdMarker = None,
        expected_bucket_owner: AccountId = None,
        request_payer: RequestPayer = None,
        **kwargs,
    ) -> ListMultipartUploadsOutput:
        store, s3_bucket = self._get_cross_account_bucket(context, bucket)
        validate_encoding_type(encoding_type)

        common_prefixes = set()
        count = 0
        is_truncated = False
        max_uploads = max_uploads or 1000
        prefix = prefix or ""
        delimiter = delimiter or ""
        if encoding_type == EncodingType.url:
            prefix = urlparse.quote(prefix)
            delimiter = urlparse.quote(delimiter)
        upload_id_marker_found = False

        if key_marker and upload_id_marker:
            multipart = s3_bucket.multiparts.get(upload_id_marker)
            if multipart:
                key = (
                    urlparse.quote(multipart.object.key) if encoding_type else multipart.object.key
                )
            else:
                # set key to None so it fails if the multipart is not Found
                key = None

            if key_marker != key:
                raise InvalidArgument(
                    "Invalid uploadId marker",
                    ArgumentName="upload-id-marker",
                    ArgumentValue=upload_id_marker,
                )

        uploads = []
        # sort by key and initiated
        all_multiparts = sorted(
            s3_bucket.multiparts.values(), key=lambda r: (r.object.key, r.initiated.timestamp())
        )
        last_multipart = all_multiparts[-1] if all_multiparts else None

        for multipart in all_multiparts:
            key = urlparse.quote(multipart.object.key) if encoding_type else multipart.object.key
            # skip all keys that are different than key_marker
            if key_marker:
                if key < key_marker:
                    continue
                elif key == key_marker:
                    if not upload_id_marker:
                        continue
                    # as the keys are ordered by time, once we found the key marker, we can return the next one
                    if multipart.id == upload_id_marker:
                        upload_id_marker_found = True
                        continue
                    elif not upload_id_marker_found:
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
            else:
                multipart_upload = MultipartUpload(
                    UploadId=multipart.id,
                    Key=multipart.object.key,
                    Initiated=multipart.initiated,
                    StorageClass=multipart.object.storage_class,
                    Owner=multipart.object.owner,
                    Initiator=multipart.initiator,
                )
                if multipart.checksum_algorithm:
                    multipart_upload["ChecksumAlgorithm"] = multipart.checksum_algorithm
                    multipart_upload["ChecksumType"] = multipart.checksum_type

                uploads.append(multipart_upload)

            count += 1
            if count >= max_uploads and last_multipart.id != multipart.id:
                is_truncated = True
                break

        common_prefixes = [CommonPrefix(Prefix=prefix) for prefix in sorted(common_prefixes)]

        response = ListMultipartUploadsOutput(
            Bucket=bucket,
            IsTruncated=is_truncated,
            MaxUploads=max_uploads or 1000,
            KeyMarker=key_marker or "",
            UploadIdMarker=upload_id_marker or "" if key_marker else "",
            NextKeyMarker="",
            NextUploadIdMarker="",
        )
        if uploads:
            response["Uploads"] = uploads
            last_upload = uploads[-1]
            response["NextKeyMarker"] = last_upload["Key"]
            response["NextUploadIdMarker"] = last_upload["UploadId"]
        if delimiter:
            response["Delimiter"] = delimiter
        if prefix:
            response["Prefix"] = prefix
        if encoding_type:
            response["EncodingType"] = EncodingType.url
        if common_prefixes:
            response["CommonPrefixes"] = common_prefixes

        return response