def test_s3_put_object_versioned(self, s3_bucket, snapshot, aws_client):
        snapshot.add_transformer(snapshot.transform.s3_api())

        # this object is put before the bucket is versioned, its internal versionId is `null`
        key = "non-version-bucket-key"
        put_obj_pre_versioned = aws_client.s3.put_object(
            Bucket=s3_bucket, Key=key, Body="non-versioned-key"
        )
        snapshot.match("put-pre-versioned", put_obj_pre_versioned)
        get_obj_pre_versioned = aws_client.s3.get_object(Bucket=s3_bucket, Key=key)
        snapshot.match("get-pre-versioned", get_obj_pre_versioned)

        list_obj_pre_versioned = aws_client.s3.list_object_versions(Bucket=s3_bucket)
        snapshot.match("list-object-pre-versioned", list_obj_pre_versioned)

        # we activate the bucket versioning then check if the object has a versionId
        aws_client.s3.put_bucket_versioning(
            Bucket=s3_bucket,
            VersioningConfiguration={"Status": "Enabled"},
        )

        get_obj_non_versioned = aws_client.s3.get_object(Bucket=s3_bucket, Key=key)
        snapshot.match("get-post-versioned", get_obj_non_versioned)

        # create versioned key, then update it, and check we got the last versionId
        key_2 = "versioned-bucket-key"
        put_obj_versioned_1 = aws_client.s3.put_object(
            Bucket=s3_bucket, Key=key_2, Body="versioned-key"
        )
        snapshot.match("put-obj-versioned-1", put_obj_versioned_1)
        put_obj_versioned_2 = aws_client.s3.put_object(
            Bucket=s3_bucket, Key=key_2, Body="versioned-key-updated"
        )
        snapshot.match("put-obj-versioned-2", put_obj_versioned_2)

        get_obj_versioned = aws_client.s3.get_object(Bucket=s3_bucket, Key=key_2)
        snapshot.match("get-obj-versioned", get_obj_versioned)

        list_obj_post_versioned = aws_client.s3.list_object_versions(Bucket=s3_bucket)
        snapshot.match("list-object-versioned", list_obj_post_versioned)

        # disable versioning to check behaviour after getting keys
        # all keys will now have versionId when getting them, even non-versioned ones
        aws_client.s3.put_bucket_versioning(
            Bucket=s3_bucket,
            VersioningConfiguration={"Status": "Suspended"},
        )
        list_obj_post_versioned_disabled = aws_client.s3.list_object_versions(Bucket=s3_bucket)
        snapshot.match("list-bucket-suspended", list_obj_post_versioned_disabled)

        get_obj_versioned_disabled = aws_client.s3.get_object(Bucket=s3_bucket, Key=key_2)
        snapshot.match("get-obj-versioned-disabled", get_obj_versioned_disabled)

        get_obj_non_versioned_disabled = aws_client.s3.get_object(Bucket=s3_bucket, Key=key)
        snapshot.match("get-obj-non-versioned-disabled", get_obj_non_versioned_disabled)

        # won't return the versionId from put
        key_3 = "non-version-bucket-key-after-disable"
        put_obj_non_version_post_disable = aws_client.s3.put_object(
            Bucket=s3_bucket, Key=key_3, Body="non-versioned-key-post"
        )
        snapshot.match("put-non-versioned-post-disable", put_obj_non_version_post_disable)
        # will return the versionId now, when it didn't before setting the BucketVersioning to `Enabled`
        get_obj_non_version_post_disable = aws_client.s3.get_object(Bucket=s3_bucket, Key=key_3)
        snapshot.match("get-non-versioned-post-disable", get_obj_non_version_post_disable)

        # manually assert all VersionId, as it's hard to do in snapshots:
        assert "VersionId" not in get_obj_pre_versioned
        assert get_obj_non_versioned["VersionId"] == "null"
        assert list_obj_pre_versioned["Versions"][0]["VersionId"] == "null"
        assert get_obj_versioned["VersionId"] is not None
        assert list_obj_post_versioned["Versions"][0]["VersionId"] == "null"
        assert list_obj_post_versioned["Versions"][1]["VersionId"] is not None
        assert list_obj_post_versioned["Versions"][2]["VersionId"] is not None