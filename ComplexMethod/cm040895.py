def delete_objects(
        self,
        context: RequestContext,
        bucket: BucketName,
        delete: Delete,
        mfa: MFA = None,
        request_payer: RequestPayer = None,
        bypass_governance_retention: BypassGovernanceRetention = None,
        expected_bucket_owner: AccountId = None,
        checksum_algorithm: ChecksumAlgorithm = None,
        **kwargs,
    ) -> DeleteObjectsOutput:
        store, s3_bucket = self._get_cross_account_bucket(context, bucket)

        if bypass_governance_retention is not None and not s3_bucket.object_lock_enabled:
            raise InvalidArgument(
                "x-amz-bypass-governance-retention is only applicable to Object Lock enabled buckets.",
                ArgumentName="x-amz-bypass-governance-retention",
            )

        objects: list[ObjectIdentifier] = delete.get("Objects")
        if not objects:
            raise MalformedXML()

        # TODO: max 1000 delete at once? test against AWS?

        quiet = delete.get("Quiet", False)
        deleted = []
        errors = []

        to_remove = []
        versioned_keys = set()
        for to_delete_object in objects:
            object_key = to_delete_object.get("Key")
            version_id = to_delete_object.get("VersionId")
            if s3_bucket.versioning_status is None:
                if version_id and version_id != "null":
                    errors.append(
                        Error(
                            Code="NoSuchVersion",
                            Key=object_key,
                            Message="The specified version does not exist.",
                            VersionId=version_id,
                        )
                    )
                    continue

                found_object = s3_bucket.objects.pop(object_key, None)
                if found_object:
                    to_remove.append(found_object)
                    self._notify(context, s3_bucket=s3_bucket, s3_object=found_object)
                    store.tags.delete_all_tags(get_unique_key_id(bucket, object_key, version_id))
                # small hack to not create a fake object for nothing
                elif s3_bucket.notification_configuration:
                    # DeleteObjects is a bit weird, even if the object didn't exist, S3 will trigger a notification
                    # for a non-existing object being deleted
                    self._notify(
                        context, s3_bucket=s3_bucket, s3_object=S3Object(key=object_key, etag="")
                    )

                if not quiet:
                    deleted.append(DeletedObject(Key=object_key))

                continue

            if not version_id:
                delete_marker_id = generate_version_id(s3_bucket.versioning_status)
                delete_marker = S3DeleteMarker(key=object_key, version_id=delete_marker_id)
                s3_bucket.objects.set(object_key, delete_marker)
                s3_notif_ctx = S3EventNotificationContext.from_request_context(
                    context,
                    s3_bucket=s3_bucket,
                    s3_object=delete_marker,
                )
                s3_notif_ctx.event_type = f"{s3_notif_ctx.event_type}MarkerCreated"
                self._notify(context, s3_bucket=s3_bucket, s3_notif_ctx=s3_notif_ctx)

                if not quiet:
                    deleted.append(
                        DeletedObject(
                            DeleteMarker=True,
                            DeleteMarkerVersionId=delete_marker_id,
                            Key=object_key,
                        )
                    )
                continue

            if not (
                found_object := s3_bucket.objects.get(object_key=object_key, version_id=version_id)
            ):
                errors.append(
                    Error(
                        Code="NoSuchVersion",
                        Key=object_key,
                        Message="The specified version does not exist.",
                        VersionId=version_id,
                    )
                )
                continue

            if found_object.is_locked(bypass_governance_retention):
                errors.append(
                    Error(
                        Code="AccessDenied",
                        Key=object_key,
                        Message="Access Denied because object protected by object lock.",
                        VersionId=version_id,
                    )
                )
                continue

            s3_bucket.objects.pop(object_key=object_key, version_id=version_id)
            versioned_keys.add(object_key)

            if not quiet:
                deleted_object = DeletedObject(
                    Key=object_key,
                    VersionId=version_id,
                )
                if isinstance(found_object, S3DeleteMarker):
                    deleted_object["DeleteMarker"] = True
                    deleted_object["DeleteMarkerVersionId"] = found_object.version_id

                deleted.append(deleted_object)

            if isinstance(found_object, S3Object):
                to_remove.append(found_object)

            self._notify(context, s3_bucket=s3_bucket, s3_object=found_object)
            store.tags.delete_all_tags(get_unique_key_id(bucket, object_key, version_id))

        for versioned_key in versioned_keys:
            # we clean up keys that do not have any object versions in them anymore
            if versioned_key not in s3_bucket.objects:
                self._preconditions_locks[bucket].pop(versioned_key, None)

        # TODO: request charged
        self._storage_backend.remove(bucket, to_remove)
        response: DeleteObjectsOutput = {}
        # AWS validated: the list of Deleted objects is unordered, multiple identical calls can return different results
        if errors:
            response["Errors"] = errors
        if not quiet:
            response["Deleted"] = deleted

        return response