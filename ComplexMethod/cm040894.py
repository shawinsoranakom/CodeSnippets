def delete_object(
        self,
        context: RequestContext,
        bucket: BucketName,
        key: ObjectKey,
        mfa: MFA = None,
        version_id: ObjectVersionId = None,
        request_payer: RequestPayer = None,
        bypass_governance_retention: BypassGovernanceRetention = None,
        expected_bucket_owner: AccountId = None,
        if_match: IfMatch = None,
        if_match_last_modified_time: IfMatchLastModifiedTime = None,
        if_match_size: IfMatchSize = None,
        **kwargs,
    ) -> DeleteObjectOutput:
        store, s3_bucket = self._get_cross_account_bucket(context, bucket)

        if bypass_governance_retention is not None and not s3_bucket.object_lock_enabled:
            raise InvalidArgument(
                "x-amz-bypass-governance-retention is only applicable to Object Lock enabled buckets.",
                ArgumentName="x-amz-bypass-governance-retention",
            )

        # TODO: this is only supported for Directory Buckets
        non_supported_precondition = None
        if if_match:
            non_supported_precondition = "If-Match"
        if if_match_size:
            non_supported_precondition = "x-amz-if-match-size"
        if if_match_last_modified_time:
            non_supported_precondition = "x-amz-if-match-last-modified-time"
        if non_supported_precondition:
            LOG.warning(
                "DeleteObject Preconditions is only supported for Directory Buckets. "
                "LocalStack does not support Directory Buckets yet."
            )
            raise NotImplementedException(
                "A header you provided implies functionality that is not implemented",
                Header=non_supported_precondition,
            )

        if s3_bucket.versioning_status is None:
            if version_id and version_id != "null":
                raise InvalidArgument(
                    "Invalid version id specified",
                    ArgumentName="versionId",
                    ArgumentValue=version_id,
                )

            found_object = s3_bucket.objects.pop(key, None)
            # TODO: RequestCharged
            if found_object:
                self._storage_backend.remove(bucket, found_object)
                self._notify(context, s3_bucket=s3_bucket, s3_object=found_object)
                store.tags.delete_all_tags(get_unique_key_id(bucket, key, version_id))

            return DeleteObjectOutput()

        if not version_id:
            delete_marker_id = generate_version_id(s3_bucket.versioning_status)
            delete_marker = S3DeleteMarker(key=key, version_id=delete_marker_id)
            s3_bucket.objects.set(key, delete_marker)
            s3_notif_ctx = S3EventNotificationContext.from_request_context(
                context,
                s3_bucket=s3_bucket,
                s3_object=delete_marker,
            )
            s3_notif_ctx.event_type = f"{s3_notif_ctx.event_type}MarkerCreated"
            self._notify(context, s3_bucket=s3_bucket, s3_notif_ctx=s3_notif_ctx)

            return DeleteObjectOutput(VersionId=delete_marker.version_id, DeleteMarker=True)

        if key not in s3_bucket.objects:
            return DeleteObjectOutput()

        if not (s3_object := s3_bucket.objects.get(key, version_id)):
            raise InvalidArgument(
                "Invalid version id specified",
                ArgumentName="versionId",
                ArgumentValue=version_id,
            )

        if s3_object.is_locked(bypass_governance_retention):
            raise AccessDenied("Access Denied because object protected by object lock.")

        s3_bucket.objects.pop(object_key=key, version_id=version_id)
        response = DeleteObjectOutput(VersionId=s3_object.version_id)

        if isinstance(s3_object, S3DeleteMarker):
            response["DeleteMarker"] = True
        else:
            self._storage_backend.remove(bucket, s3_object)
            store.tags.delete_all_tags(get_unique_key_id(bucket, key, version_id))
        self._notify(context, s3_bucket=s3_bucket, s3_object=s3_object)

        if key not in s3_bucket.objects:
            # we clean up keys that do not have any object versions in them anymore
            self._preconditions_locks[bucket].pop(key, None)

        return response